"""Punto 2: procedencia e independencia de fuentes. "7 notas, 2 procedencias independientes" (pregunta fija del jurado)."""
import os
import tempfile

os.environ["LLM_OFFLINE"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db, main, scoring  # noqa: E402
from app.agent import events, pipeline  # noqa: E402
from app.agent.corpus import Noticia  # noqa: E402
from app.agent.embed import embed  # noqa: E402
from app.models import Ficha  # noqa: E402


def noticia(i, titulo, medio, url=None):
    return Noticia(i, titulo, url or f"https://{medio}/{i}", medio, "es", "2026-10-01T10:00:00+00:00", "", "gdelt")


def procedencias(*ns):
    miem = list(zip(ns, embed([n.titulo for n in ns])))
    return events.procedencias(miem, None), events.resumen_procedencias(list(ns), events.procedencias(miem, None))


def test_agencia_replicada_por_cinco_medios_cuenta_una():
    ns = [noticia(f"A{i}", f"(EFE) Panamá y Costa Rica firman acuerdo aduanero", m) for i, m in
          enumerate(["a.com", "b.com", "c.com", "d.com", "e.com"])]
    proc, res = procedencias(*ns)
    assert len(set(proc.values())) == 1 and res[0]["nombre"] == "Agencia EFE" and res[0]["notas"] == 5


def test_mismo_dominio_con_dos_notas_cuenta_una():
    proc, res = procedencias(noticia("M1", "Moody evalúa el grado de inversión de Panamá este año", "prensa.com"),
                             noticia("M2", "Las razones del cierre de la mina según el Gobierno", "prensa.com"))
    assert len(set(proc.values())) == 1 and res[0]["notas"] == 2 and res[0]["etiqueta"] == "medio:prensa.com"


def test_dominio_raiz_de_replicas_y_nota_propia_es_una_sola_procedencia():
    """Regresión: prensa.com aparecía como 'replica:prensa.com' y también como 'medio:prensa.com' (dos fuentes)."""
    t = "S & P ratifica el grado de inversión de Panamá en BBB y mantiene perspectiva estable"
    ns = [noticia("P1", t, "prensa.com"), noticia("P2", t, "diaadia.com.pa"), noticia("P3", t + " según el MEF", "revistaeyn.com"),
          noticia("P4", "Las razones y advertencias de la calificadora para mantener el grado a Panamá", "prensa.com"),
          noticia("P5", "Calificación crediticia: lo que dijo otro análisis independiente sobre la economía", "laestrella.com.pa")]
    proc, res = procedencias(*ns)
    assert proc["P4"] == proc["P1"] and len(set(proc.values())) == 2  # grupo prensa.com + laestrella
    prensa = next(r for r in res if r["nombre"] == "prensa.com")
    assert prensa["notas"] == 4 and set(prensa["medios"]) == {"prensa.com", "diaadia.com.pa", "revistaeyn.com"}


def test_medios_distintos_con_titulares_distintos_son_independientes():
    proc, _ = procedencias(noticia("D1", "Sinaproc extiende vigilancia por lluvias hasta el viernes", "tvn-2.com"),
                           noticia("D2", "Alerta de lluvias y vientos fuertes en todo el país esta semana", "telemetro.com"))
    assert len(set(proc.values())) == 2


@pytest.fixture(scope="module")
def fichas():
    return {f.id_caso: f for f in pipeline.analizar()["fichas"]}


def test_ficha_trae_notas_totales_y_procedencias_independientes(fichas):
    f = fichas["EV-G226d8217c0"]  # S&P: 6 titulares de varios medios
    assert f.fuentes_totales == f.registros == 6 and f.procedencias_independientes == f.fuentes_independientes == 3
    assert sum(p["notas"] for p in f.procedencias) == f.fuentes_totales and len(f.procedencias) == f.procedencias_independientes


def test_caso_sintetico_de_agencia_replicada(fichas):
    f = fichas["SINT-S-DUP-001"]
    assert (f.fuentes_totales, f.procedencias_independientes) == (3, 1) and f.procedencias[0]["nombre"] == "Agencia EFE"
    assert any("no cuenta como corroboración" in a for a in f.alertas)


def test_la_puntuacion_usa_procedencias_no_notas(fichas):
    """E y 'estado de evidencia' dependen de las procedencias independientes: repetir una nota no mejora la evidencia."""
    f = fichas["SINT-S-DUP-001"]
    assert f.estado_evidencia != "suficiente_para_borrador" and f.componentes.E < 0.7


# ---- reseed al cambiar la versión de las fichas conserva el trabajo humano
def test_resembrar_conserva_revisiones_y_borradores(monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "reseed.db"))
    monkeypatch.setattr(main.agent, "AGENT_MODE", "live")
    monkeypatch.setattr(main.agent, "build_candidates", lambda: pipeline.seleccionar(pipeline.analizar()["fichas"])[:20])
    db.init()
    main.sembrar()
    una = db.inbox(1, False)[1][0]["id_caso"]
    f = Ficha(**db.get(una))
    f.estado_revision, f.revisiones, f.borrador = "en_revision", [{"estado": "en_revision", "revisor": "Ana", "comentario": "ok", "ts": "t"}], {"titulo": "X"}
    db.save(f)
    db.set_meta("fichas_version", "viejo")  # simula una base creada por una versión anterior
    with TestClient(main.app):  # el arranque detecta la versión distinta y regenera
        pass
    g = Ficha(**db.get(una))
    assert g.estado_revision == "en_revision" and g.revisiones[0]["revisor"] == "Ana" and g.borrador == {"titulo": "X"}
    assert db.get_meta("fichas_version") == main.FICHAS_VERSION
