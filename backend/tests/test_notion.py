"""Export a Notion generado desde el sistema (punto 8): cada número sale de una fuente del sistema, nada inventado."""
import json
import os
import tempfile

os.environ["LLM_OFFLINE"] = "1"

import pytest  # noqa: E402

from app import db, notion_export as nx, scoring  # noqa: E402
from app.agent import pipeline  # noqa: E402
from app.models import Ficha  # noqa: E402

INFORME = {"generado_utc": "2026-10-07T03:00:00+00:00", "segundos": 9.1, "verdes": 9, "total": 10, "comando": "pytest",
           "filas": [{"id": f"T{i:02d}", "titulo": f"caso {i}", "esperado": "esp", "estado": "rojo" if i == 5 else "verde", "motivo": "",
                      "pruebas": [{"prueba": f"test_T{i:02d}_x", "ok": i != 5, "segundos": 0.5,
                                   "mensaje": "AssertionError: 3 != 40" if i == 5 else "", "comprueba": ""}]}
                     for i in range(1, 11)]}


@pytest.fixture
def base(monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "notion.db"))
    db.init()
    db.replace_all([scoring.aplicar(f) for f in pipeline.seleccionar(pipeline.analizar()["fichas"])])


def test_matriz_refleja_la_corrida_tal_cual():
    md = nx.matriz_md(INFORME, {"generado_utc": "2026-10-07T00:00:00+00:00", "tabla": [
        {"metrica": "Citas válidas", "agente": "194/194 (100%)", "baseline": "—", "nota": "",
         "agente_nd": {"num": 194, "den": 194}, "baseline_nd": None}]})
    assert "**9/10 en verde**" in md and "2026-10-06 22:00 (Panamá)" in md
    assert "| T05 |" in md and "ROJO · 0/1 pruebas — AssertionError: 3 != 40" in md
    assert md.count("VERDE · 1/1") == 9 and "| Citas válidas | 194/194 | — |" in md


def test_sin_corrida_ni_metricas_queda_pendiente():
    md = nx.matriz_md({"disponible": False}, None)
    assert md.count("PENDIENTE") == 2 and "VERDE" not in md


def test_catalogo_sale_del_manifest():
    m = json.loads((db.DATA_DIR / "raw" / "manifest.json").read_text(encoding="utf-8"))
    md = nx.catalogo_md(m)
    for nombre, a in m["archivos"].items():
        assert f"| `{nombre}` | {a['registros']} | `{a['sha256']}` |" in md
    assert f"**fallidas:** {len(m['consultas_fallidas'])}" in md and m["licencia_condiciones"] in md


def test_bitacora_usa_revisiones_reales_o_pendiente(base):
    assert "PENDIENTE: aún no hay revisiones" in nx.bitacora_md([], db.all_fichas(), [])
    d = db.all_fichas()[0]
    d["revisiones"] = [{"estado": "descartado", "revisor": "Editora X", "comentario": "duplicado", "ts": "2026-10-07T15:00:00+00:00"}]
    db.save(Ficha(**d))
    db.log("review", d["id_caso"], "descartado por Editora X: duplicado")
    dec = nx.decisiones_de_docs("| D01 | 2026-10-06 | Modalidad TVN | x | y |\n| D02 | 2026-10-06 | RSS | a | b |")
    md = nx.bitacora_md(db.audit(), db.all_fichas(), dec)
    assert "| 2026-10-07 10:00 (Panamá) | `" + d["id_caso"] + "` | descartado | Editora X | duplicado |" in md
    assert "| review | 1 |" in md and "| D02 | 2026-10-06 | RSS |" in md


def test_exportar_escribe_las_cuatro_paginas_con_cinco_fichas_y_una_insuficiente(base):
    destino = tempfile.mkdtemp()
    rutas = nx.exportar(destino, informe=INFORME)
    assert set(rutas) == {"10_matriz_T01_T10.md", "11_catalogo_generado.md", "05_casos_y_evidencias.md", "12_bitacora_y_revisiones.md"}
    fichas = rutas["05_casos_y_evidencias.md"].read_text(encoding="utf-8")
    assert fichas.count("## Ficha ") >= 5 and "no encontrada" not in fichas
    assert "Estado de evidencia | **insuficiente**" in fichas
    assert "| Persona revisora | PENDIENTE |" in fichas  # nadie revisó en esta base: no se inventa
