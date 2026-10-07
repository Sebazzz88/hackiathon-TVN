"""Punto 1: evidencia verificable en CÓDIGO, no en el prompt.
El validador posterior al LLM elimina toda afirmación cuya cita no exista en el corpus o cuyo campo no contenga lo citado,
y registra cuántas eliminó. Cada cita se puede abrir hasta su registro fuente."""
import json
import os
import tempfile

os.environ["LLM_OFFLINE"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db, main  # noqa: E402
from app.agent import corpus, draft, pipeline  # noqa: E402

ID = "G11b756ff2a"   # laestrella.com.pa: «S & P ratifica grado de inversión de Panamá en BBB - y mantiene perspectiva estable, dice el MEF»
CITA = [{"id_evidencia": ID, "campo": "titulo"}]


@pytest.fixture(scope="module")
def ev():
    f = next(f for f in pipeline.analizar()["fichas"] if ID in f.ids_fuente)
    return draft.evidencias(f)


def validar(texto, tipo, ev, citas=CITA):
    return draft.validar([{"texto": texto, "tipo": tipo, "citas": citas}], ev, "t")


def test_cita_a_id_inexistente_en_el_corpus_se_elimina(ev):
    ok, fuera = validar("Según un medio, el PIB subió.", "declaracion", ev, [{"id_evidencia": "Gzzzzzzzzzz", "campo": "titulo"}])
    assert not ok and fuera[0]["codigo"] == "fuera_del_corpus"


def test_cita_a_evidencia_real_pero_ajena_a_la_ficha_se_distingue(ev):
    otro = next(n for n in corpus.noticias() if n.id not in ev)
    ok, fuera = validar("Según otro medio, algo ocurrió.", "declaracion", ev, [{"id_evidencia": otro.id, "campo": "titulo"}])
    assert not ok and fuera[0]["codigo"] == "fuera_de_ficha"  # existe en el corpus, pero no respalda ESTA ficha


def test_campo_que_no_contiene_lo_afirmado_se_elimina(ev):
    """El id existe y el campo existe, pero el titular no dice eso."""
    ok, fuera = validar("Según laestrella.com.pa, el Gobierno anunció un nuevo subsidio eléctrico para jubilados.", "declaracion", ev)
    assert not ok and fuera[0]["codigo"] == "sin_sustento" and "no contiene lo afirmado" in fuera[0]["motivo"]


def test_campo_que_si_contiene_lo_afirmado_pasa(ev):
    ok, fuera = validar("Según laestrella.com.pa, S & P ratificó el grado de inversión de Panamá con perspectiva estable.", "declaracion", ev)
    assert len(ok) == 1 and not fuera


def test_entrecomillado_debe_ser_literal_del_campo(ev):
    ok, fuera = validar("laestrella.com.pa publicó: «S & P rebaja la calificación de Panamá a BB».", "declaracion", ev)
    assert not ok and "entrecomillado" in fuera[0]["motivo"]
    ok, _ = validar("laestrella.com.pa publicó: «S & P ratifica grado de inversión de Panamá en BBB - y mantiene perspectiva estable, dice el MEF».", "declaracion", ev)
    assert len(ok) == 1


def test_inferencia_no_se_contrasta_palabra_a_palabra_pero_si_necesita_cita(ev):
    ok, _ = validar("Esto podría influir en el costo del financiamiento público.", "inferencia", ev)
    assert len(ok) == 1
    ok, fuera = validar("Esto podría influir en el costo del financiamiento público.", "inferencia", ev, citas=[])
    assert not ok and fuera[0]["codigo"] == "sin_cita"


def test_cada_eliminada_trae_codigo_y_el_resumen_cuenta(ev):
    afirms = [
        {"texto": "Según laestrella.com.pa, S & P ratificó el grado de inversión de Panamá.", "tipo": "declaracion", "citas": CITA},
        {"texto": "Frase sin cita.", "tipo": "hecho", "citas": []},
        {"texto": "La inflación llegó a 45%.", "tipo": "hecho", "citas": CITA},
        {"texto": "Según X.", "tipo": "declaracion", "citas": [{"id_evidencia": "Gnoexiste00", "campo": "titulo"}]},
        {"texto": "Según laestrella.com.pa, el Gobierno anunció un nuevo subsidio eléctrico para jubilados.", "tipo": "declaracion", "citas": CITA},
    ]
    ok, fuera = draft.validar(afirms, ev, "brief")
    r = draft.resumen_validador(len(afirms), fuera)
    assert (r["emitidas"], r["validas"], r["eliminadas"]) == (5, 1, 4)
    assert r["por_codigo"] == {"sin_cita": 1, "cifras": 1, "fuera_del_corpus": 1, "sin_sustento": 1}


def test_el_borrador_registra_cuantas_elimino():
    f = next(f for f in pipeline.analizar()["fichas"] if f.id_caso == "SINT-S-INY-001")
    b = draft.generar(f)
    assert b["validador"]["eliminadas"] == len(b["eliminadas"]) >= 1
    assert b["validador"]["validas"] + b["validador"]["eliminadas"] == b["validador"]["emitidas"]


# ---- API: registro fuente de cada cita y totales del validador
@pytest.fixture(scope="module")
def cliente():
    mp = pytest.MonkeyPatch()
    mp.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "evidencia.db"))
    db.init()
    with TestClient(main.app) as c:
        yield c
    mp.undo()


@pytest.mark.parametrize("id_ev,tipo,campo", [
    (ID, "noticia", "titulo"),
    ("WB:PAN:FP.CPI.TOTL.ZG:2023", "indicador", "valor"),
    ("AGR:EV-G226d8217c0", "agrupacion", "metodo"),
])
def test_cada_cita_abre_su_registro_fuente(cliente, id_ev, tipo, campo):
    r = cliente.get(f"/api/evidencia/{id_ev}")
    assert r.status_code == 200
    d = r.json()
    assert d["tipo"] == tipo and campo in d["campos"] and d["nota"]


def test_registro_de_noticia_separa_publicacion_de_deteccion(cliente):
    d = cliente.get(f"/api/evidencia/{ID}").json()
    assert d["campos"]["fecha_publicacion"] is None and d["campos"]["fecha_deteccion"]  # GDELT: solo detección
    assert "DETECCIÓN" in d["nota"] and d["url"].startswith("http")


def test_registro_de_indicador_trae_pais_anio_unidad(cliente):
    c = cliente.get("/api/evidencia/WB:PAN:FP.CPI.TOTL.ZG:2023").json()["campos"]
    assert (c["pais"], c["anio"], c["unidad"]) == ("PAN", 2023, "% anual")


def test_sismo_trae_magnitud_lugar_y_hora(cliente):
    usgs = next(i for i in corpus.registro_evidencia() if i.startswith("USGS:"))
    c = cliente.get(f"/api/evidencia/{usgs}").json()["campos"]
    assert c["magnitude"] and c["place"] and c["time"]


def test_evidencia_inexistente_es_404_con_mensaje(cliente):
    r = cliente.get("/api/evidencia/NO-EXISTE")
    assert r.status_code == 404 and "no existe en el corpus" in r.json()["detail"]


def test_totales_del_validador_se_acumulan_en_el_registro(cliente):
    antes = cliente.get("/api/validador").json()
    db.log("validador", "X", json.dumps({"emitidas": 10, "validas": 8, "eliminadas": 2, "por_codigo": {"cifras": 1, "sin_cita": 1}}))
    despues = cliente.get("/api/validador").json()
    assert despues["emitidas"] == antes["emitidas"] + 10 and despues["eliminadas"] == antes["eliminadas"] + 2
    assert despues["por_codigo"].get("cifras", 0) == antes["por_codigo"].get("cifras", 0) + 1
