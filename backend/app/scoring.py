"""P = 30R + 25I + 20U + 15N + 10E (sección 4 del reto). Empates: mayor U, luego ID."""
VERSION = "reglas-v1"
PESOS = {"R": 30, "I": 25, "U": 20, "N": 15, "E": 10}


def puntaje(c) -> float:
    return round(sum(PESOS[k] * min(1.0, max(0.0, getattr(c, k))) for k in PESOS), 2)


def banda(p: float) -> str:
    return "bajo" if p < 40 else "medio" if p < 70 else "alto"


def clave_orden(f):
    return (-f.puntaje, -f.componentes.U, f.id_caso)


def aplicar(f):
    f.puntaje = puntaje(f.componentes)
    f.banda = banda(f.puntaje)
    f.reglas_version = VERSION
    return f
