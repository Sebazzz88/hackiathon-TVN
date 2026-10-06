#!/usr/bin/env python3
"""Etapa 1 (Cargar): valida noticias.csv sin bloquear la carga (T01). Escribe data/processed/."""
import csv, json
from datetime import datetime
from pathlib import Path

D = Path(__file__).resolve().parents[1]
(D / "processed").mkdir(exist_ok=True)
rows = list(csv.DictReader(open(D / "raw/noticias.csv", encoding="utf-8")))


def fecha_ok(s):
    if not s: return True  # nulo permitido: no se rellena
    try: datetime.fromisoformat(s.replace("Z", "+00:00")); return True
    except ValueError: return False


ok, bad, ids = [], [], set()
for r in rows:
    e = []
    if not r["id_noticia"]: e.append("id vacío")
    if r["id_noticia"] in ids: e.append("id duplicado")
    if not r["url"].startswith(("http://", "https://")): e.append("url inválida")
    if not r["titulo"].strip(): e.append("título vacío")
    e += [f"{c} inválida" for c in ("fecha_publicacion", "fecha_deteccion") if not fecha_ok(r[c])]
    ids.add(r["id_noticia"])
    (bad if e else ok).append({**r, "errores": "; ".join(e)})

cols = list(rows[0].keys()) if rows else []
for name, data, extra in (("noticias_ok.csv", ok, []), ("noticias_errores.csv", bad, ["errores"])):
    with open(D / "processed" / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols + ["errores"], extrasaction="ignore")
        w.writeheader(); w.writerows(data)

origen = {}
for r in rows: origen[r["origen"]] = origen.get(r["origen"], 0) + 1
rep = {"disponible": True, "total": len(rows), "validas": len(ok), "con_error": len(bad),
       "sin_fecha_publicacion": sum(1 for r in rows if not r["fecha_publicacion"]), "por_origen": origen}
(D / "processed" / "quality_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
print(rep)
