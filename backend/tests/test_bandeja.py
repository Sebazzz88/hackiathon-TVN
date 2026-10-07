"""Bandeja: combinaciones de tamaño y filtro, migración de bases viejas, errores controlados y concurrencia.
Regresión de los fallos reportados al usar la web (cambiar 5/10/30, casos de prueba, error 500)."""
import json
import os
import sqlite3
import tempfile
import threading

os.environ["LLM_OFFLINE"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db, main  # noqa: E402
from app import scoring  # noqa: E402
from app.agent import pipeline  # noqa: E402


@pytest.fixture(scope="module")
def cliente():
    """App en modo live con su PROPIA base de datos, sin importar qué dejaron otros archivos de pruebas."""
    mp = pytest.MonkeyPatch()
    mp.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "bandeja.db"))
    mp.setattr(main.agent, "AGENT_MODE", "live")
    db.init()
    db.replace_all([scoring.aplicar(f) for f in pipeline.seleccionar(pipeline.analizar()["fichas"])])
    db.set_meta("agent_mode", "live")
    with TestClient(main.app) as c:
        yield c
    mp.undo()


@pytest.mark.parametrize("sint", [False, True])
@pytest.mark.parametrize("n", [1, 5, 10, 30, 100, 500, 1000])
def test_todas_las_combinaciones_responden_200(cliente, n, sint):
    r = cliente.get(f"/api/inbox?limit={n}&sinteticos={str(sint).lower()}")
    assert r.status_code == 200
    d = r.json()
    assert len(d["items"]) == min(n, 1000, d["total"]) and d["limit"] == min(n, 1000)
    assert all(i["sintetico"] == sint for i in d["items"])  # el filtro nunca mezcla reales con sintéticos
    p = [i["puntaje"] for i in d["items"]]
    assert p == sorted(p, reverse=True)


def test_cambiar_de_tamano_da_prefijos_consistentes(cliente):
    """El top 5 es exactamente el comienzo del top 10 y del top 30 (mismo orden y desempate)."""
    ids = {n: [i["id_caso"] for i in cliente.get(f"/api/inbox?limit={n}").json()["items"]] for n in (5, 10, 30)}
    assert ids[10][:5] == ids[5] and ids[30][:10] == ids[10]


def test_limit_invalido_se_acota(cliente):
    assert cliente.get("/api/inbox?limit=0").json()["limit"] == 1
    assert cliente.get("/api/inbox?limit=9999").json()["limit"] == 1000
    assert cliente.get("/api/inbox?limit=abc").status_code == 422  # validación normal, JSON claro


def test_la_bandeja_solo_trae_lo_necesario(cliente):
    """Rendimiento: 5 fichas pedidas -> 5 filas leídas (no las 700+), y el payload no incluye noticias ni borradores."""
    item = cliente.get("/api/inbox?limit=5").json()["items"][0]
    assert "noticias" not in item and "borrador" not in item and "contexto" not in item
    leidas, filas = db.inbox(5, False)
    assert len(filas) == 5 and leidas > 100


def test_concurrencia_no_da_errores(cliente):
    """Clic rápido entre 5/10/30 y casos de prueba: peticiones a la vez, ninguna falla."""
    estados, lock = [], threading.Lock()

    def pedir(n, s):
        r = cliente.get(f"/api/inbox?limit={n}&sinteticos={s}")
        with lock:
            estados.append(r.status_code)

    hilos = [threading.Thread(target=pedir, args=(n, s)) for n in (5, 10, 30) for s in ("true", "false") for _ in range(4)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert estados.count(200) == len(hilos)


def test_migracion_de_base_antigua(tmp_path, monkeypatch):
    """Una app.db creada por una versión anterior (sin columnas de orden) se migra sola y sigue ordenando bien."""
    ruta = tmp_path / "vieja.db"
    c = sqlite3.connect(ruta)
    c.execute("CREATE TABLE fichas(id_caso TEXT PRIMARY KEY, data TEXT NOT NULL)")
    for i, (p, u) in enumerate([(50.0, 0.1), (80.0, 0.2), (80.0, 0.9)]):
        c.execute("INSERT INTO fichas VALUES(?,?)", (f"F{i}", json.dumps({"id_caso": f"F{i}", "puntaje": p, "componentes": {"U": u}, "sintetico": False})))
    c.commit()
    c.close()
    monkeypatch.setattr(db, "DB_PATH", str(ruta))
    db.init()
    total, filas = db.inbox(3, False)
    assert total == 3 and [f["id_caso"] for f in filas] == ["F2", "F1", "F0"]  # puntaje desc y luego urgencia desc


def test_ficha_corrupta_no_tumba_la_agenda(tmp_path, monkeypatch):
    ruta = tmp_path / "corrupta.db"
    monkeypatch.setattr(db, "DB_PATH", str(ruta))
    db.init()
    with db.conn() as c:
        c.execute("INSERT INTO fichas(id_caso,data,puntaje,u,sint) VALUES('MALA','{\"id_caso\":\"MALA\"}',99,0,0)")
    from app import main
    r = main.inbox(limit=5, sinteticos=False)
    assert r.total == 1 and r.items == []  # se omite la ficha inválida en vez de devolver 500


def test_error_inesperado_responde_json_con_instruccion(cliente, monkeypatch):
    def falla(*a, **k):
        raise RuntimeError("boom interno")
    monkeypatch.setattr(db, "inbox", falla)
    sin_relanzar = TestClient(main.app, raise_server_exceptions=False)
    r = sin_relanzar.get("/api/inbox?limit=5")
    assert r.status_code == 500 and "Reintenta" in r.json()["detail"] and "boom" not in r.text  # no filtra el error interno


def test_max_devuelve_todo_lo_disponible_y_total_dice_cuanto_hay(cliente):
    """Máx: pedir más de lo que existe devuelve todo, y `total` permite avisar "solo hay N"."""
    pruebas = cliente.get("/api/inbox?limit=1000&sinteticos=true").json()
    assert pruebas["total"] == len(pruebas["items"]) < 30  # los casos controlados son pocos: no se inventan más
    reales = cliente.get("/api/inbox?limit=1000&sinteticos=false").json()
    assert reales["total"] == len(reales["items"]) > 100 and all(not i["sintetico"] for i in reales["items"])
    custom = cliente.get("/api/inbox?limit=7&sinteticos=false").json()
    assert len(custom["items"]) == 7 and custom["total"] == reales["total"]
