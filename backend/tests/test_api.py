"""API en modo stub (datos DEMO). Independiente del orden de las pruebas: usa su PROPIA base temporal y fija el modo y las
funciones stub aquí mismo (antes dependía de ser el primer archivo en importar la app y podía escribir en data/app.db)."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app import db, main, scoring
from app.models import Componentes, Ficha, QueryOut


def _stub_fichas():
    demo = [("DEMO-001", (0.9, 0.7, 0.8, 0.6, 0.5), "parcial"),
            ("DEMO-002", (0.95, 0.9, 0.9, 0.8, 0.1), "insuficiente"),
            ("DEMO-003", (0.4, 0.3, 0.2, 0.5, 0.7), "suficiente_para_borrador")]
    return [Ficha(id_caso=i, titulo=f"[DEMO] {i}", ids_fuente=[f"{i}-S1"], estado_evidencia=e, sintetico=True,
                  componentes=Componentes(R=c[0], I=c[1], U=c[2], N=c[3], E=c[4])) for i, c, e in demo]


@pytest.fixture()
def cliente(monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "api.db"))
    monkeypatch.setattr(main.agent, "AGENT_MODE", "stub")
    monkeypatch.setattr(main.agent, "build_candidates", _stub_fichas)
    monkeypatch.setattr(main.agent, "answer_query", lambda p, ia=False: QueryOut(abstencion=True, estado="abstencion",
                                                                                 faltante=["Agente en modo stub"]))
    with TestClient(main.app) as c:
        yield c


def test_formula_y_bandas():
    assert scoring.puntaje(Componentes(R=1, I=1, U=1, N=1, E=1)) == 100
    assert scoring.puntaje(Componentes(R=0, I=0, U=0, N=0, E=0)) == 0
    assert scoring.banda(39.99) == "bajo" and scoring.banda(40) == "medio" and scoring.banda(70) == "alto"


def test_bandeja_ordenada_y_aprobacion_bloqueada(cliente):
    items = cliente.get("/api/inbox").json()["items"]
    assert [i["puntaje"] for i in items] == sorted((i["puntaje"] for i in items), reverse=True)
    r = cliente.post("/api/fichas/DEMO-002/review", json={"estado": "aprobado_como_borrador", "revisor": "Ana"})
    assert r.status_code == 409  # T08: prioridad alta + evidencia insuficiente no habilita aprobar


def test_consulta_sin_corpus_se_abstiene_y_valida_entrada(cliente):
    assert cliente.post("/api/query", json={"pregunta": "¿Cuál fue la inflación hoy?"}).json()["abstencion"] is True
    assert cliente.post("/api/query", json={"pregunta": "x" * 501}).status_code == 422


def test_las_pruebas_no_tocan_la_base_real(cliente):
    assert os.path.basename(db.DB_PATH) == "api.db" and os.path.realpath(tempfile.gettempdir()) in os.path.realpath(db.DB_PATH)
