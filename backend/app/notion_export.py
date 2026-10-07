"""Páginas de Notion generadas DESDE EL SISTEMA (punto 8): nada se escribe a mano, todo sale de una fuente verificable.

  10_matriz_T01_T10.md          ← resultado de correr T01–T10 (app/jurado.py) + métricas de eval/results.json
  11_catalogo_generado.md       ← data/raw/manifest.json (archivos, registros, SHA-256, consultas, licencias)
  05_casos_y_evidencias.md      ← fichas del pipeline (≥5 reales, una con evidencia insuficiente) + su revisión humana
  12_bitacora_y_revisiones.md   ← tabla audit de la base (revisiones humanas, borradores, validador) + docs/09_DECISIONS.md

Uso:  cd backend; .\\.venv\\Scripts\\python -m app.notion_export            (usa la última corrida de T01–T10)
      cd backend; .\\.venv\\Scripts\\python -m app.notion_export --correr   (corre T01–T10 antes de exportar)
Lo que el sistema no sabe (p. ej. persona revisora de una ficha sin revisar) queda como PENDIENTE, nunca inventado.
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path

from . import db, jurado, scoring
from .agent import draft, pipeline
from .agent.config import PANAMA_TZ, TEMAS
from .agent.corpus import parse_dt

DESTINO = db.ROOT / "docs" / "notion_export"

CASOS = [
    ("EV-G226d8217c0", "CU-02: tema económico con serie oficial del Banco Mundial (dato anual, no de hoy)"),
    ("EV-Gb01bc434a8", "Tema económico con 3 procedencias independientes"),
    ("EV-T7bb199ba28", "Caso SIN evidencia suficiente: prioridad alta, una sola fuente"),
    ("EV-G97e3e7b0a7", "CU-03: titulares en varios idiomas agrupados; réplicas cuentan como una fuente"),
    ("EV-G1454ad17a8", "Evento natural con contexto USGS (solo hechos sísmicos)"),
    ("SINT-S-CON-001", "CU-04 / T05 (sintético): versiones incompatibles visibles, sin elegir"),
    ("SINT-S-INY-001", "T07 (sintético): fuente que intenta cambiar las instrucciones"),
]
NOMBRES = {"R": "Relevancia", "I": "Impacto", "U": "Urgencia", "N": "Novedad", "E": "Evidencia"}


def hora_pa(iso):
    """'2026-10-07T03:10:00+00:00' → '2026-10-06 22:10 (Panamá)'. Sin fecha → '—'; ilegible → tal cual."""
    if not iso:
        return "—"
    d = parse_dt(str(iso))
    return d.astimezone(PANAMA_TZ).strftime("%Y-%m-%d %H:%M") + " (Panamá)" if d else str(iso)


def _celda(x):
    return str(x if x not in (None, "") else "—").replace("|", "/").replace("\n", " ")


def _tabla(cab, filas):
    return ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(_celda(c) for c in f) + " |" for f in filas]


# ------------------------------------------------------------------ 10 · matriz T01–T10
def matriz_md(informe, metricas):
    L = ["# Pruebas y métricas (generado)", "",
         "Generado por `backend/app/notion_export.py` a partir de la última ejecución real de las pruebas "
         "(`backend/app/jurado.py`, la misma que corre el botón «Modo jurado») y de `eval/results.json`.", ""]
    if not informe or informe.get("disponible") is False:
        L += ["**PENDIENTE:** aún no hay una ejecución de T01–T10 registrada en este equipo. "
              "Corre `python -m app.notion_export --correr` o el botón del Modo jurado.", ""]
    else:
        L += [f"Ejecución: {hora_pa(informe['generado_utc'])} · {informe['segundos']} s · "
              f"**{informe['verdes']}/{informe['total']} en verde** · comando `{informe.get('comando', '')}`", ""]
        filas = []
        for f in informe["filas"]:
            pruebas = f["pruebas"]
            obs = ("VERDE" if f["estado"] == "verde" else "ROJO") + f" · {sum(p['ok'] for p in pruebas)}/{len(pruebas)} pruebas"
            evid = "; ".join(f"`{p['prueba']}` {'PASSED' if p['ok'] else 'FAILED'} ({p['segundos']} s)" for p in pruebas) or f["motivo"]
            fallo = "; ".join(p["mensaje"][:160] for p in pruebas if not p["ok"] and p["mensaje"])
            filas.append([f["id"], f["titulo"], f["esperado"], obs + (f" — {fallo}" if fallo else ""), evid])
        L += _tabla(["ID", "Caso", "Resultado esperado", "Resultado observado", "Evidencia de ejecución"], filas)
        L += ["", "Las correcciones aplicadas tras cada fallo están en `06_pruebas_y_metricas.md` y `docs/10_CHANGELOG.md`.", ""]
    L += ["## Agente frente a baseline", ""]
    if not metricas or metricas.get("disponible") is False:
        L += ["**PENDIENTE:** falta `eval/results.json` (correr `eval/run_eval.py`).", ""]
    else:
        nd = lambda x, v: f"{x['num']}/{x['den']}" if x else _celda(v)  # noqa: E731
        L += [f"Fuente: `eval/results.json` · ejecución {hora_pa(metricas.get('generado_utc'))} · {metricas.get('conjunto', '')}. "
              f"{metricas.get('etiquetas', '')}", ""]
        L += _tabla(["Métrica", "Agente (IA)", "Baseline", "Nota"],
                    [[t["metrica"], nd(t.get("agente_nd"), t["agente"]), nd(t.get("baseline_nd"), t["baseline"]), t.get("nota", "")]
                     for t in metricas.get("tabla", [])])
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ 11 · catálogo
def catalogo_md(m):
    if not m:
        return "# Catálogo de datos (generado)\n\n**PENDIENTE:** falta `data/raw/manifest.json`.\n"
    L = ["# Catálogo de datos (generado)", "",
         f"Generado desde `data/raw/manifest.json` (versión `{m.get('version')}`). Corte del snapshot: "
         f"**{hora_pa(m.get('fecha_corte_UTC'))}** ({m.get('fecha_corte_UTC')} UTC).", ""]
    L += _tabla(["Archivo", "Registros", "SHA-256"],
                [[f"`{k}`", v.get("registros"), f"`{v.get('sha256')}`"] for k, v in m.get("archivos", {}).items()])
    L += ["", f"**Licencias y condiciones:** {m.get('licencia_condiciones', '—')}", "",
          f"**Ventana de noticias:** {m.get('ventana_noticias_dias', '—')} días. {m.get('nota_intervalo', '')}", "",
          "**Transformaciones:**", ""] + [f"- {t}" for t in m.get("transformaciones", [])]
    fallidas = m.get("consultas_fallidas", [])
    L += ["", f"**Consultas ejecutadas:** {len(m.get('consultas', []))} · **fallidas:** {len(fallidas)}. {m.get('nota_cobertura', '')}", ""]
    if fallidas:
        L += ["<details><summary>Consultas fallidas</summary>", ""] + [f"- {x}" for x in fallidas] + ["", "</details>", ""]
    L += ["**Consultas (URL exactas):**", ""] + [f"- {u}" for u in m.get("consultas", [])]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ 05 · fichas
def md_ficha(f, motivo, n, borrador, revisiones=()):
    """Una ficha trazable. `revisiones` son las de la base (persona, estado, comentario); si no hay, PENDIENTE."""
    f = scoring.aplicar(f.model_copy())  # copia: las fichas del pipeline están en caché y no se modifican
    b = borrador
    ult = revisiones[-1] if revisiones else None
    L = [f"## Ficha {n} · {f.titulo}", "", f"**Por qué este caso:** {motivo}", "",
         "| Campo | Valor |", "|---|---|",
         f"| ID del caso | `{f.id_caso}` |",
         "| Modalidad | TVN editorial |",
         f"| Tema | {TEMAS.get(f.tema, f.tema)} |",
         f"| Sintético | {'Sí (caso controlado de prueba)' if f.sintetico else 'No'} |",
         f"| Puntaje | **{f.puntaje}/100** ({f.banda}) · reglas `{f.reglas_version}` |",
         f"| Estado de evidencia | **{f.estado_evidencia.replace('_', ' ')}** |",
         f"| Notas / procedencias independientes | {f.fuentes_totales or f.registros} / {f.procedencias_independientes or f.fuentes_independientes} |",
         f"| Base | {f.base} |",
         f"| Estado de revisión | {ult['estado'].replace('_', ' ') + ' · ' + hora_pa(ult.get('ts')) if ult else 'PENDIENTE (sin revisión registrada en el sistema)'} |",
         f"| Persona revisora | {_celda(ult.get('revisor')) if ult else 'PENDIENTE'} |"]
    if ult and ult.get("comentario"):
        L.append(f"| Comentario de revisión | {_celda(ult['comentario'])} |")
    L += ["", "**Puntaje desglosado** (P = 30R + 25I + 20U + 15N + 10E)", "",
          "| Componente | Valor 0–1 | Aporte | Justificación |", "|---|---|---|---|"]
    for k, w in scoring.PESOS.items():
        v = getattr(f.componentes, k)
        L.append(f"| {k} · {NOMBRES[k]} | {v:.2f} | {v * w:.1f} | {_celda(f.justificacion.get(k, ''))} |")
    L += ["", "**Fuentes (IDs del snapshot)**", "",
          "| ID | Medio | Procedencia | Publicación | Detección | Titular |", "|---|---|---|---|---|---|"]
    for x in f.noticias:
        L.append(f"| `{x['id']}` | {_celda(x['medio'])} | {_celda(x['procedencia'])} | {hora_pa(x.get('fecha_publicacion'))} | "
                 f"{hora_pa(x.get('fecha_deteccion'))} | [{_celda(x['titulo'])}]({x['url']}) |")
    if f.contexto:
        L += ["", "**Contexto oficial**", ""] + [f"- {c['texto']} (`{c['id_evidencia']}`). {c['limitacion']}" for c in f.contexto]
    if f.contradicciones:
        L += ["", "**Versiones incompatibles**", ""]
        for k in f.contradicciones:
            L += [f"- {v['medio']}: «{v['titulo']}» (`{v['id']}`)" for v in k["versiones"]]
    if f.alertas:
        L += ["", "**Alertas**", ""] + [f"- {a}" for a in f.alertas]
    L += ["", "**Qué falta comprobar**", ""] + [f"- {x}" for x in f.faltante]
    L += ["", f"**Acción recomendada:** {f.accion}", "",
          f"**Borrador** (generador `{b.get('generador')}`; {b.get('aviso', '')})", ""]
    if b.get("afirmaciones"):
        L += [f"- Título: {b['titulo']}"]
        L += [f"- [{a['tipo']}] ({a['seccion']}) {a['texto']} — " + ", ".join(f"`{c['id_evidencia']}·{c['campo']}`" for c in a["citas"])
              for a in b["afirmaciones"]]
        L += ["- Preguntas: " + " / ".join(b["preguntas"]),
              f"- Brief {b['brief_palabras']}/250 palabras · guion ~{b['guion_segundos_estimados']} s · copy {b['copy_palabras']}/80 palabras",
              f"- Afirmaciones eliminadas por el validador: {len(b.get('eliminadas', []))}"
              + "".join(f"\n  - «{e['texto']}» — {e['motivo']}" for e in b.get("eliminadas", []))]
    else:
        L += [f"- Sin borrador: {'; '.join(b.get('faltante', []))}"]
    L += ["", "---", ""]
    return "\n".join(L)


def fichas_md(fichas, revisiones_por_caso, corte_utc=None):
    out = ["# Casos y evidencias (fichas trazables)", "",
           "Generado por `backend/app/notion_export.py` desde el snapshot congelado"
           + (f" (corte {hora_pa(corte_utc)})" if corte_utc else "") + ". "
           "Cinco fichas reales, una de ellas con evidencia insuficiente, y dos casos sintéticos de prueba. "
           "La revisión humana sale de la base del sistema; si no hay, queda PENDIENTE.", ""]
    for n, (cid, motivo) in enumerate(CASOS, 1):
        f = fichas.get(cid)
        if not f:
            out.append(f"## Ficha {n} · `{cid}` no encontrada en el snapshot actual\n")
            continue
        out.append(md_ficha(f, motivo, n, draft.generar(f), revisiones_por_caso.get(cid, [])))
    return "\n".join(out)


# ------------------------------------------------------------------ 12 · bitácora
def decisiones_de_docs(texto):
    """Filas de la tabla de decisiones de docs/09_DECISIONS.md: [(id, fecha, decisión)]."""
    return [(m.group(1), m.group(2), m.group(3).strip()) for m in
            re.finditer(r"^\|\s*(D\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+)\|", texto, re.M)]


def bitacora_md(audit, fichas_db, decisiones):
    revs = [(r.get("ts"), d["id_caso"], r) for d in fichas_db for r in d.get("revisiones", [])]
    revs.sort(key=lambda x: x[0] or "")
    cuenta = Counter(a["accion"] for a in audit)
    L = ["# Bitácora de decisiones y revisiones humanas (generado)", "",
         "Generado por `backend/app/notion_export.py` desde la tabla `audit` y las fichas de la base del sistema "
         "(`data/app.db`), más la tabla de decisiones de `docs/09_DECISIONS.md`. Horas en Panamá.", "",
         "## Revisiones humanas registradas", ""]
    if revs:
        L += _tabla(["Fecha", "Caso", "Decisión", "Persona", "Comentario"],
                    [[hora_pa(ts), f"`{cid}`", r["estado"].replace("_", " "), r.get("revisor"), r.get("comentario")] for ts, cid, r in revs])
    else:
        L += ["PENDIENTE: aún no hay revisiones humanas registradas en el sistema. Se registran en la pestaña de revisión de cada ficha."]
    L += ["", "## Actividad del sistema (tabla audit)", ""]
    if audit:
        L += _tabla(["Acción", "Veces"], sorted(cuenta.items(), key=lambda x: -x[1]))
        L += ["", "Últimos 20 eventos:", ""]
        L += _tabla(["Fecha", "Acción", "Caso", "Detalle"],
                    [[hora_pa(a["ts"]), a["accion"], a.get("id_caso"), (a.get("detalle") or "")[:140]] for a in audit[:20]])
    else:
        L += ["Sin eventos registrados todavía."]
    L += ["", "## Decisiones de diseño", "", "Fuente: `docs/09_DECISIONS.md` (alternativas y justificación completas allí).", ""]
    L += _tabla(["#", "Fecha", "Decisión"], decisiones) if decisiones else ["PENDIENTE: no se encontró la tabla de decisiones."]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ orquestación
def exportar(destino=DESTINO, correr=False, informe=None):
    """Escribe las 4 páginas y devuelve {archivo: ruta}. `informe` permite inyectar una corrida (pruebas)."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    if informe is None:
        informe = jurado.correr() if correr else jurado.ultimo()
    metricas = db.leer_json(db.ROOT / "eval" / "results.json")
    manifest = db.leer_json(db.DATA_DIR / "raw" / "manifest.json")
    db.init()
    fichas_db = db.all_fichas()
    p_dec = db.ROOT / "docs" / "09_DECISIONS.md"
    decisiones = decisiones_de_docs(p_dec.read_text(encoding="utf-8")) if p_dec.exists() else []
    fichas = {f.id_caso: f for f in pipeline.analizar()["fichas"]}
    paginas = {
        "10_matriz_T01_T10.md": matriz_md(informe, metricas),
        "11_catalogo_generado.md": catalogo_md(manifest),
        "05_casos_y_evidencias.md": fichas_md(fichas, {d["id_caso"]: d.get("revisiones", []) for d in fichas_db},
                                              (manifest or {}).get("fecha_corte_UTC")),
        "12_bitacora_y_revisiones.md": bitacora_md(db.audit(), fichas_db, decisiones),
    }
    rutas = {}
    for nombre, texto in paginas.items():
        (destino / nombre).write_text(texto, encoding="utf-8")
        rutas[nombre] = destino / nombre
    return rutas


if __name__ == "__main__":
    os.environ["LLM_OFFLINE"] = "1"  # sin red y reproducible: los borradores de las fichas salen de la caché o de la plantilla
    for ruta in exportar(correr="--correr" in sys.argv).values():
        print("escrito", ruta)
