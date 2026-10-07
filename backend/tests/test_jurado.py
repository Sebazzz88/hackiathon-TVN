"""Punto 6: Modo jurado. El botón corre T01–T10 en vivo y muestra verde/rojo con evidencia; las métricas salen de
eval/results.json (generado por eval/run_eval.py, nunca escrito a mano)."""
import json

from app import jurado
from app.db import ROOT


def test_correr_t01_a_t10_da_verde_con_evidencia():
    r = jurado.correr()
    assert r["total"] == 10 and [f["id"] for f in r["filas"]] == [f"T{i:02d}" for i in range(1, 11)]
    for f in r["filas"]:
        assert f["estado"] == "verde", (f["id"], f["pruebas"])
        assert f["esperado"] and f["pruebas"] and all(p["comprueba"] and p["segundos"] >= 0 for p in f["pruebas"])
    assert r["verdes"] == 10 and jurado.ultimo()["generado_utc"] == r["generado_utc"]


def test_metricas_salen_de_results_json_con_numerador_y_denominador():
    d = json.loads((ROOT / "eval" / "results.json").read_text(encoding="utf-8"))
    filas = {t["metrica"]: t for t in d["tabla"]}
    abst = next(t for n, t in filas.items() if n.startswith("[reservado] Abstención correcta"))
    assert abst["agente_nd"]["den"] > 0 and abst["agente_nd"]["num"] <= abst["agente_nd"]["den"]
    assert all(t["agente_nd"] is None or isinstance(t["agente_nd"]["num"], int) for t in d["tabla"])
