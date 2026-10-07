#!/usr/bin/env python3
"""Evaluación reproducible: agente (IA) vs baseline (palabras clave / reglas / fecha). Sección 9.1 del reto.

Uso (desde la raíz del repo):
    backend\\.venv\\Scripts\\python eval\\run_eval.py            # dev + reservado, reporte separado
    backend\\.venv\\Scripts\\python eval\\run_eval.py --solo dev

Entradas:  eval/benchmark.jsonl (60 consultas: 40 dev / 20 reservado), eval/etiquetas_temas.csv,
           eval/etiquetas_pares.csv, eval/seleccion_editor.json (opcional, para Precision@5).
Salidas:   eval/resultados/resumen.json (lo lee la UI), eval/resultados/detalle_*.jsonl,
           eval/resultados/afirmaciones_para_revision.csv (validez de sustento: revisión humana), REPORTE.md.
Se reporta numerador/denominador y cada fallo; no se esconden errores tras un promedio.
"""
import csv
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend"))
os.environ.setdefault("LLM_OFFLINE", os.getenv("EVAL_LLM_OFFLINE", "1"))  # por defecto: sin red ni costo

from app.agent import baseline, draft, pipeline, query  # noqa: E402
from app.agent.config import TEMAS  # noqa: E402
from app.agent.corpus import registro_evidencia  # noqa: E402
from app.agent.events import jaccard, titulo_base  # noqa: E402

EV = RAIZ / "eval"
OUT = EV / "resultados"


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))] if xs else None


def frac(n, d):
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "0/0 (sin casos)"


def leer_csv(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------ consultas
def baseline_responder(pregunta, noticias):
    """Baseline: búsqueda por palabras clave sobre titulares; responde con el primer resultado o se abstiene si no
    hay ninguna palabra en común. No conoce los indicadores ni detecta contradicciones o inyecciones."""
    res = baseline.buscar(pregunta, noticias, k=1)
    if not res:
        return {"abstencion": True, "ids": [], "versiones": False, "texto": ""}
    _, n = res[0]
    return {"abstencion": False, "ids": [n.id], "versiones": False, "texto": n.titulo}


def correcto(caso, abst, ids, versiones, texto):
    e = caso["esperado"]
    if caso["tipo"] in ("sin_respuesta", "adversarial"):
        return abst and not ids
    if caso["tipo"] == "contradiccion":
        return (not abst) and versiones and set(e["ids_requeridos"]) <= set(ids)
    ok = (not abst) and bool(set(e.get("ids_aceptables", [])) & set(ids))
    for frag in e.get("debe_contener", []):
        ok = ok and frag.lower() in (texto or "").lower()
    return ok


def eval_consultas(casos, noticias):
    det, tiempos = [], []
    for c in casos:
        t0 = time.perf_counter()
        r = query.responder(c["pregunta"])
        dt = time.perf_counter() - t0
        tiempos.append(dt)
        ids = [x.id_evidencia for x in r.citas]
        ag_ok = correcto(c, r.abstencion, ids, bool(r.versiones), r.respuesta)
        b = baseline_responder(c["pregunta"], noticias)
        b_ok = correcto(c, b["abstencion"], b["ids"], b["versiones"], b["texto"])
        det.append({"id": c["id"], "particion": c["particion"], "tipo": c["tipo"], "pregunta": c["pregunta"],
                    "agente": {"correcto": ag_ok, "abstencion": r.abstencion, "ids": ids, "versiones": len(r.versiones),
                               "metodo": r.metodo, "segundos": round(dt, 3), "respuesta": r.respuesta, "faltante": r.faltante},
                    "baseline": {"correcto": b_ok, "abstencion": b["abstencion"], "ids": b["ids"]},
                    "esperado": c["esperado"]})
    return det, tiempos


def resumen_consultas(det):
    m = {}
    for tipo in ("sustentada", "contradiccion", "sin_respuesta", "adversarial"):
        d = [x for x in det if x["tipo"] == tipo]
        m[tipo] = {"agente": (sum(x["agente"]["correcto"] for x in d), len(d)),
                   "baseline": (sum(x["baseline"]["correcto"] for x in d), len(d)),
                   "fallos_agente": [x["id"] for x in d if not x["agente"]["correcto"]]}
    noresp = [x for x in det if x["tipo"] in ("sin_respuesta", "adversarial")]
    resp = [x for x in det if x["tipo"] in ("sustentada", "contradiccion")]
    m["abstencion_correcta"] = {"agente": (sum(x["agente"]["abstencion"] and not x["agente"]["ids"] for x in noresp), len(noresp)),
                                "baseline": (sum(x["baseline"]["abstencion"] for x in noresp), len(noresp))}
    m["abstencion_incorrecta"] = {"agente": (sum(x["agente"]["abstencion"] for x in resp), len(resp)),
                                  "baseline": (sum(x["baseline"]["abstencion"] for x in resp), len(resp))}
    return m


# ------------------------------------------------------------------ clasificación y agrupación
def macro_f1(y, p, clases):
    f1s, por = [], {}
    for c in clases:
        tp = sum(1 for a, b in zip(y, p) if a == c and b == c)
        fp = sum(1 for a, b in zip(y, p) if a != c and b == c)
        fn = sum(1 for a, b in zip(y, p) if a == c and b != c)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        if tp + fn:  # solo clases presentes en las etiquetas
            f1s.append(f)
        por[c] = {"precision": round(pr, 3), "recall": round(rc, 3), "f1": round(f, 3), "soporte": tp + fn}
    return (round(sum(f1s) / len(f1s), 3) if f1s else None), por


def eval_temas(a):
    p = EV / "etiquetas_temas.csv"
    if not p.exists():
        return None
    filas = leer_csv(p)
    idx = {n.id: i for i, n in enumerate(a["noticias"])}
    out = {}
    for part in ("dev", "test"):
        f = [r for r in filas if r["particion"] == part and r["id_noticia"] in idx]
        y = [r["tema_humano"] for r in f]
        ag = [a["clas"][idx[r["id_noticia"]]][0] for r in f]
        bl = [baseline.clasificar(r["titulo"]) for r in f]
        fa, pa = macro_f1(y, ag, list(TEMAS))
        fb, pb = macro_f1(y, bl, list(TEMAS))
        out[part] = {"n": len(f), "macro_f1_agente": fa, "macro_f1_baseline": fb,
                     "exactitud_agente": frac(sum(1 for u, v in zip(y, ag) if u == v), len(f)),
                     "exactitud_baseline": frac(sum(1 for u, v in zip(y, bl) if u == v), len(f)),
                     "por_clase_agente": pa, "por_clase_baseline": pb,
                     "errores_agente": [{"id": r["id_noticia"], "titulo": r["titulo"], "humano": u, "agente": v}
                                        for r, u, v in zip(f, y, ag) if u != v]}
    out["metodo"] = filas[0].get("etiquetado_por", "") if filas else ""
    return out


def eval_pares(a):
    p = EV / "etiquetas_pares.csv"
    if not p.exists():
        return None
    filas = leer_csv(p)
    grupo = {}
    for gi, g in enumerate(a["grupos"]):
        for i in g:
            grupo[a["noticias"][i].id] = gi
    tit = {n.id: n.titulo for n in a["noticias"]}

    def prf(pred, y):
        tp = sum(1 for u, v in zip(y, pred) if u and v)
        fp = sum(1 for u, v in zip(y, pred) if not u and v)
        fn = sum(1 for u, v in zip(y, pred) if u and not v)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        return {"precision": frac(tp, tp + fp), "recall": frac(tp, tp + fn),
                "f1": round(2 * pr * rc / (pr + rc), 3) if pr + rc else 0.0}
    f = [r for r in filas if r["id_a"] in grupo and r["id_b"] in grupo]
    y = [r["mismo_evento"] == "1" for r in f]
    ag = [grupo[r["id_a"]] == grupo[r["id_b"]] for r in f]
    bl = [jaccard(titulo_base(tit[r["id_a"]]), titulo_base(tit[r["id_b"]])) >= 0.5 for r in f]
    return {"n": len(f), "agente": prf(ag, y), "baseline_jaccard_0.5": prf(bl, y),
            "errores_agente": [{"a": tit[r["id_a"]], "b": tit[r["id_b"]], "humano": u, "agente": v}
                               for r, u, v in zip(f, y, ag) if u != v],
            "metodo": f[0].get("etiquetado_por", "") if f else ""}


# ------------------------------------------------------------------ borradores y citas
def eval_borradores(a):
    sel = pipeline.seleccionar(a["fichas"])
    reales = [f for f in sel if not f.sintetico][:10]
    sint = [f for f in sel if f.sintetico]
    reg = registro_evidencia()
    det, tiempos, filas = [], [], []
    for f in reales + sint:
        t0 = time.perf_counter()
        b = draft.generar(f)
        tiempos.append(time.perf_counter() - t0)
        ev = draft.evidencias(f)
        afs = b.get("afirmaciones", [])
        validas = sum(1 for x in afs if x["citas"] and all(
            (c["id_evidencia"] in ev and c["campo"] in ev[c["id_evidencia"]]) and
            (c["id_evidencia"].startswith("AGR:") or c["id_evidencia"] in reg) for c in x["citas"]))
        det.append({"id_caso": f.id_caso, "sintetico": f.sintetico, "generador": b.get("generador"),
                    "emitidas": len(afs), "con_cita_valida": validas, "eliminadas": len(b.get("eliminadas", [])),
                    "brief_palabras": b.get("brief_palabras"), "copy_palabras": b.get("copy_palabras"),
                    "guion_s": b.get("guion_segundos_estimados"), "preguntas": len(b.get("preguntas", [])),
                    "leyenda": b.get("brief", "").startswith("Basado únicamente en titular/metadatos")})
        for x in afs:
            for c in x["citas"]:
                d = ev.get(c["id_evidencia"], {})
                filas.append({"id_caso": f.id_caso, "seccion": x["seccion"], "tipo": x["tipo"], "afirmacion": x["texto"],
                              "id_evidencia": c["id_evidencia"], "campo": c["campo"],
                              "texto_evidencia": str(d.get(c["campo"], ""))[:300],
                              "veredicto_humano (respaldada/no_respaldada)": "", "revisor": ""})
    return det, tiempos, filas


# ------------------------------------------------------------------ ranking
def eval_ranking(a):
    top_ag = [f.id_caso for f in pipeline.seleccionar(a["fichas"]) if not f.sintetico][:5]
    grupos = [{"id": f.id_caso, "fecha_ultima": f.fecha_ultima} for f in a["fichas"] if not f.sintetico]
    top_bl = [g["id"] for g in baseline.ranking_por_fecha(grupos)[:5]]
    tit = {f.id_caso: f.titulo for f in a["fichas"]}
    out = {"top5_agente": [(i, tit[i]) for i in top_ag], "top5_baseline_fecha": [(i, tit[i]) for i in top_bl],
           "coincidencia_agente_baseline": frac(len(set(top_ag) & set(top_bl)), 5)}
    p = EV / "seleccion_editor.json"
    if p.exists():
        sel_ed = set(json.loads(p.read_text(encoding="utf-8"))["ids"])
        out["precision_at_5_agente"] = frac(len(set(top_ag) & sel_ed), 5)
        out["precision_at_5_baseline"] = frac(len(set(top_bl) & sel_ed), 5)
        out["nota"] = "Exploratoria: selección independiente de una sola persona."
    else:
        out["precision_at_5_agente"] = "PENDIENTE"
        out["nota"] = "Falta eval/seleccion_editor.json (selección independiente de un editor). No se reporta Precision@5."
    return out


def main():
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    pipeline.analizar.cache_clear()
    a = pipeline.analizar()
    t_pipe = time.perf_counter() - t0
    casos = [json.loads(linea) for linea in (EV / "benchmark.jsonl").read_text(encoding="utf-8").splitlines() if linea.strip()]
    noticias = a["noticias"]
    res = {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "particiones": {}}
    tiempos_q = []
    for part in ("dev", "reservado"):
        if solo and part != solo:
            continue
        cs = [c for c in casos if c["particion"] == part]
        det, t = eval_consultas(cs, noticias)
        tiempos_q += t
        with open(OUT / f"detalle_{part}.jsonl", "w", encoding="utf-8") as fh:
            for d in det:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        res["particiones"][part] = resumen_consultas(det)
    temas = eval_temas(a)
    pares = eval_pares(a)
    bdet, t_b, filas = eval_borradores(a)
    with open(OUT / "afirmaciones_para_revision.csv", "w", newline="", encoding="utf-8") as fh:
        if filas:
            w = csv.DictWriter(fh, fieldnames=list(filas[0]))
            w.writeheader()
            w.writerows(filas)
    rank = eval_ranking(a)
    em, cv = sum(d["emitidas"] for d in bdet), sum(d["con_cita_valida"] for d in bdet)
    res.update({
        "temas": temas, "agrupacion": pares, "borradores": bdet, "ranking": rank,
        "tiempos": {"pipeline_s": round(t_pipe, 2), "consulta_mediana_s": round(statistics.median(tiempos_q), 3),
                    "consulta_p95_s": round(p95(tiempos_q), 3), "borrador_mediana_s": round(statistics.median(t_b), 3),
                    "borrador_p95_s": round(p95(t_b), 3), "n_consultas": len(tiempos_q), "n_borradores": len(t_b),
                    "entorno": "CPU local Windows, embeddings ONNX locales, LLM desactivado (plantilla/caché)"},
        "costo": "0 USD en esta ejecución (LLM_OFFLINE=1: plantilla determinista o caché).",
    })
    # ---- tabla para la UI
    met = []
    for part, m in res["particiones"].items():
        for k, nom in (("sustentada", "Respuestas sustentadas correctas"), ("contradiccion", "Contradicciones mostradas"),
                       ("sin_respuesta", "Sin respuesta: abstención correcta"), ("adversarial", "Adversariales rechazadas")):
            met.append({"nombre": f"[{part}] {nom}", "agente": frac(*m[k]["agente"]), "baseline": frac(*m[k]["baseline"]),
                        "nota": ("Fallos: " + ", ".join(m[k]["fallos_agente"])) if m[k]["fallos_agente"] else "sin fallos"})
        met.append({"nombre": f"[{part}] Abstención correcta (sin respuesta + adversarial)", "agente": frac(*m["abstencion_correcta"]["agente"]),
                    "baseline": frac(*m["abstencion_correcta"]["baseline"]), "nota": "meta ≥ 80%"})
        met.append({"nombre": f"[{part}] Abstención INCORRECTA en respondibles", "agente": frac(*m["abstencion_incorrecta"]["agente"]),
                    "baseline": frac(*m["abstencion_incorrecta"]["baseline"]), "nota": "menor es mejor"})
    met.append({"nombre": "Cobertura de citas en borradores", "agente": frac(cv, em), "baseline": None,
                "nota": f"{sum(d['eliminadas'] for d in bdet)} afirmaciones eliminadas por el validador; validez de sustento: PENDIENTE revisión humana (afirmaciones_para_revision.csv)"})
    if temas:
        for part in ("dev", "test"):
            met.append({"nombre": f"Clasificación temática macro-F1 [{part}, n={temas[part]['n']}]",
                        "agente": temas[part]["macro_f1_agente"], "baseline": temas[part]["macro_f1_baseline"],
                        "nota": f"exactitud {temas[part]['exactitud_agente']} vs {temas[part]['exactitud_baseline']}"})
    if pares:
        met.append({"nombre": f"Agrupación de eventos (pares, n={pares['n']}) F1", "agente": pares["agente"]["f1"],
                    "baseline": pares["baseline_jaccard_0.5"]["f1"],
                    "nota": f"P {pares['agente']['precision']} · R {pares['agente']['recall']}"})
    met.append({"nombre": "Precision@5 (exploratoria)", "agente": rank["precision_at_5_agente"],
                "baseline": rank.get("precision_at_5_baseline"), "nota": rank["nota"]})
    met.append({"nombre": "Tiempo por consulta (mediana / p95)", "agente": f"{res['tiempos']['consulta_mediana_s']} s / {res['tiempos']['consulta_p95_s']} s",
                "baseline": None, "nota": f"meta mediana ≤ 15 s; pipeline completo {res['tiempos']['pipeline_s']} s"})
    met.append({"nombre": "Tiempo por borrador (mediana / p95)", "agente": f"{res['tiempos']['borrador_mediana_s']} s / {res['tiempos']['borrador_p95_s']} s",
                "baseline": None, "nota": res["costo"]})
    res["metricas"] = met
    res["conjunto"] = f"{len(casos)} consultas ({sum(c['particion'] == 'dev' for c in casos)} dev / {sum(c['particion'] == 'reservado' for c in casos)} reservadas)"
    res["etiquetas"] = ("Propuestas por el asistente de IA (Claude) a partir de titulares y del snapshot; "
                        "PENDIENTE revisión humana. Hasta entonces las métricas son preliminares.")
    (OUT / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    # eval/results.json: lo que lee el Modo jurado. Numerador y denominador salen de los mismos valores calculados arriba.
    def _nd(v):
        m = re.match(r"\s*(\d+)/(\d+)", str(v)) if v is not None else None
        return {"num": int(m.group(1)), "den": int(m.group(2))} if m else None

    tabla = [{"metrica": m["nombre"], "agente": m["agente"], "baseline": m["baseline"], "nota": m["nota"],
              "agente_nd": _nd(m["agente"]), "baseline_nd": _nd(m["baseline"])} for m in met]
    (EV / "results.json").write_text(json.dumps({"generado_utc": res["generado_utc"], "conjunto": res["conjunto"],
                                                 "etiquetas": res["etiquetas"], "tabla": tabla, "tiempos": res["tiempos"],
                                                 "costo": res["costo"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    # ---- reporte legible
    L = [f"# Resultados de evaluación — {res['generado_utc']}", "", f"Conjunto: {res['conjunto']}. {res['etiquetas']}", "",
         "| Métrica | Agente (IA) | Baseline | Nota |", "|---|---|---|---|"]
    L += [f"| {m['nombre']} | {m['agente']} | {m['baseline'] if m['baseline'] is not None else '—'} | {m['nota']} |" for m in met]
    L += ["", "## Top 5 del agente vs baseline por fecha", ""]
    L += [f"{i + 1}. {t} (`{x}`)" for i, (x, t) in enumerate(rank["top5_agente"])]
    L += ["", "Baseline (más reciente primero):", ""] + [f"{i + 1}. {t} (`{x}`)" for i, (x, t) in enumerate(rank["top5_baseline_fecha"])]
    if temas:
        L += ["", "## Errores de clasificación del agente (test)", ""]
        L += [f"- «{e['titulo']}» humano={e['humano']} agente={e['agente']}" for e in temas["test"]["errores_agente"]]
    (OUT / "REPORTE.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # "≥" y acentos también si la salida va a un archivo
    print("\n".join(L))


if __name__ == "__main__":
    main()
