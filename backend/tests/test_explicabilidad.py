"""Punto 5: explicabilidad del puntaje. En TODAS las fichas: valor 0-1 por componente, peso, aporte que suma el puntaje,
una frase de por qué y la versión de reglas visible."""
from app import scoring
from app.agent import pipeline


def test_cada_ficha_explica_su_puntaje():
    for f in pipeline.seleccionar(pipeline.analizar()["fichas"]):
        aportes = {k: scoring.PESOS[k] * getattr(f.componentes, k) for k in scoring.PESOS}
        assert abs(sum(aportes.values()) - f.puntaje) < 0.06, f.id_caso
        assert all(0 <= getattr(f.componentes, k) <= 1 for k in scoring.PESOS)
        assert set(f.justificacion) == set(scoring.PESOS) and all(len(f.justificacion[k]) > 10 for k in scoring.PESOS)
        assert f.reglas_version == scoring.VERSION and f.banda == scoring.banda(f.puntaje)


def test_pesos_del_reto_sin_cambios():
    assert scoring.PESOS == {"R": 30, "I": 25, "U": 20, "N": 15, "E": 10} and scoring.VERSION == "reglas-v1"
