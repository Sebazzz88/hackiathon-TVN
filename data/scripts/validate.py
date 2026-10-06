#!/usr/bin/env python3
"""Etapa 1 (Cargar): valida el snapshot sin bloquear la carga (T01) y emite data/processed/quality_report.json.

- noticias.csv: IDs (vacíos/duplicados), URL, campos obligatorios, fechas ISO 8601, filas nulas, intervalo.
  Las filas con error se separan en noticias_errores.csv; las válidas van a noticias_ok.csv. Nulos se conservan.
- indicadores.csv: cuadrícula esperada 6×6×15 = 1.350, valores nulos contados (nunca rellenados con 0).
- eventos.geojson: campos mínimos del contrato y caja regional.
Uso: python data/scripts/validate.py [carpeta_raw] [carpeta_processed]
"""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

D = Path(__file__).resolve().parents[1]
OBLIG = ["id_noticia", "titulo", "url", "medio", "fecha_extraccion", "origen"]
COLS = ["id_noticia", "titulo", "url", "medio", "idioma", "fecha_publicacion", "fecha_deteccion", "fecha_extraccion",
        "tema", "origen", "alcance_texto"]


def fecha(s):
    """None si vacío (nulo permitido), datetime si válida, False si inválida."""
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return False


def limpiar_titulo(t):
    """GDELT tokeniza con espacios antes de la puntuación ('1 , 500', 'Panamá : ...'). Se corrige solo el espaciado;
    el texto original queda intacto en data/raw/noticias.csv."""
    t = re.sub(r"(\d) ([.,]) (\d)", r"\1\2\3", t)
    t = re.sub(r"\s+([,.:;?!%)])", r"\1", t)
    t = re.sub(r"([¿¡(])\s+", r"\1", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def validar_noticias(rows):
    ok, bad, ids, urls = [], [], set(), set()
    for r in rows:
        r = {k: (v or "").strip() if isinstance(v, str) else (v or "") for k, v in r.items() if k}
        e = []
        if not any(r.get(c) for c in COLS):
            e.append("fila nula")
        else:
            e += [f"{c} vacío" for c in OBLIG if not r.get(c)]
            if r.get("id_noticia") and r["id_noticia"] in ids:
                e.append("id duplicado")
            if r.get("url") and not r["url"].startswith(("http://", "https://")):
                e.append("url inválida")
            if r.get("url") and r["url"] in urls:
                e.append("url duplicada")
            for c in ("fecha_publicacion", "fecha_deteccion", "fecha_extraccion"):
                if fecha(r.get(c, "")) is False:
                    e.append(f"{c} inválida")
            if not r.get("fecha_publicacion") and not r.get("fecha_deteccion"):
                e.append("sin fecha de publicación ni de detección")
        ids.add(r.get("id_noticia"))
        urls.add(r.get("url"))
        if r.get("titulo"):
            r["titulo"] = limpiar_titulo(r["titulo"])
        (bad if e else ok).append({**r, "errores": "; ".join(e)})
    return ok, bad


def validar(raw: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    rep = {"disponible": True, "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    p = raw / "noticias.csv"
    rows = list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if p.exists() else []
    ok, bad = validar_noticias(rows)
    for name, data in (("noticias_ok.csv", ok), ("noticias_errores.csv", bad)):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS + ["errores"], extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
    origen, errores = {}, {}
    for r in ok:
        origen[r["origen"]] = origen.get(r["origen"], 0) + 1
    for r in bad:
        for e in r["errores"].split("; "):
            errores[e] = errores.get(e, 0) + 1
    fechas = [d for r in ok for d in [fecha(r.get("fecha_publicacion")) or fecha(r.get("fecha_deteccion"))] if d]
    rep["noticias"] = {
        "total": len(rows), "validas": len(ok), "con_error": len(bad), "errores_por_tipo": errores,
        "por_origen_validas": origen, "tvn_validas": origen.get("tvn_rss", 0),
        "sin_fecha_publicacion": sum(1 for r in ok if not r.get("fecha_publicacion")),
        "medios_distintos": len({r["medio"] for r in ok}),
        "cobertura": {"desde": min(fechas).isoformat() if fechas else None, "hasta": max(fechas).isoformat() if fechas else None},
        "cumple_minimo_100": len(ok) >= 100, "cumple_minimo_20_tvn": origen.get("tvn_rss", 0) >= 20,
    }
    # compatibilidad con la UI previa
    rep.update({"total": len(rows), "validas": len(ok), "con_error": len(bad), "por_origen": origen,
                "sin_fecha_publicacion": rep["noticias"]["sin_fecha_publicacion"]})
    p = raw / "indicadores.csv"
    if p.exists():
        ind = list(csv.DictReader(open(p, encoding="utf-8", newline="")))
        esperadas = len({r["pais_iso3"] for r in ind}) * len({r["indicador_id"] for r in ind}) * len({r["anio"] for r in ind})
        rep["indicadores"] = {"celdas": len(ind), "esperadas": esperadas,
                              "nota": "6 países × 6 indicadores × 15 años = 540 celdas. El PDF menciona 1.350, cifra que no "
                                      "corresponde a esa cuadrícula; se conserva la cuadrícula completa con nulos explícitos.", "con_valor": sum(1 for r in ind if r["valor"].strip()),
                              "nulas": sum(1 for r in ind if not r["valor"].strip()),
                              "paises": sorted({r["pais_iso3"] for r in ind}), "indicadores": sorted({r["indicador_id"] for r in ind}),
                              "anios": [min(int(r["anio"]) for r in ind), max(int(r["anio"]) for r in ind)] if ind else []}
    p = raw / "eventos.geojson"
    if p.exists():
        fs = json.loads(p.read_text(encoding="utf-8")).get("features", [])
        falt = sum(1 for f in fs if f["properties"].get("mag") is None or not f.get("id") or not f["properties"].get("url"))
        fuera = sum(1 for f in fs if not (5 <= f["geometry"]["coordinates"][1] <= 12 and -86 <= f["geometry"]["coordinates"][0] <= -76))
        mags = [f["properties"]["mag"] for f in fs if f["properties"].get("mag") is not None]
        rep["eventos"] = {"total": len(fs), "con_campos_faltantes": falt, "fuera_de_caja": fuera,
                          "magnitud_max": max(mags) if mags else None,
                          "nota": "Caja regional lat 5–12, lon −86/−76; no equivale al territorio de Panamá."}
    (out / "quality_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


if __name__ == "__main__":
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else D / "raw"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else D / "processed"
    print(json.dumps(validar(raw, out), ensure_ascii=False, indent=2))
