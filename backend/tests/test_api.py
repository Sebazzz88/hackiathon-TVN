import os, tempfile
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")
os.environ["AGENT_MODE"] = "stub"
from fastapi.testclient import TestClient
from app.main import app
from app import scoring
from app.models import Componentes


def test_formula_y_bandas():
    assert scoring.puntaje(Componentes(R=1, I=1, U=1, N=1, E=1)) == 100
    assert scoring.puntaje(Componentes(R=0, I=0, U=0, N=0, E=0)) == 0
    assert scoring.banda(39.99) == "bajo" and scoring.banda(40) == "medio" and scoring.banda(70) == "alto"


def test_bandeja_ordenada_y_aprobacion_bloqueada():
    with TestClient(app) as c:
        items = c.get("/api/inbox").json()["items"]
        assert [i["puntaje"] for i in items] == sorted((i["puntaje"] for i in items), reverse=True)
        r = c.post("/api/fichas/DEMO-002/review", json={"estado": "aprobado_como_borrador", "revisor": "Ana"})
        assert r.status_code == 409  # T08: prioridad alta + evidencia insuficiente no habilita aprobar


def test_consulta_sin_corpus_se_abstiene_y_valida_entrada():
    with TestClient(app) as c:
        assert c.post("/api/query", json={"pregunta": "¿Cuál fue la inflación hoy?"}).json()["abstencion"] is True
        assert c.post("/api/query", json={"pregunta": "x" * 501}).status_code == 422
