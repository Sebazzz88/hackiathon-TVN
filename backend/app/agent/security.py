"""Controles anti-inyección (T07). El texto de una fuente es DATO, nunca instrucción.

1) Detección: patrones de instrucciones dentro de titulares o consultas -> alerta visible y E=0 para ese registro.
2) Aislamiento: en el prompt del LLM cada evidencia va dentro de <DATO id=...> con caracteres de control
   neutralizados; las instrucciones viven solo en el mensaje de sistema.
3) Salida: el validador descarta afirmaciones sin cita válida, así que un texto inyectado no puede
   introducir hechos nuevos ni cambiar el puntaje (el puntaje lo calcula código, no el LLM).
"""
import re

from .baseline import norm

PATRONES = [
    r"ignor\w* (todas |las |tus |all |previous |the )*(instrucciones|instructions|reglas|rules)",
    r"olvida\w* (tus |las )?(instrucciones|reglas)",
    r"(revela|muestra|dime|reveal|print|show)\w* (tu |la |el |your |the )?(clave|api ?key|contrasena|password|secreto|secret|system prompt|prompt del sistema|token)",
    r"(system prompt|prompt del sistema|jailbreak|modo desarrollador|developer mode)",
    r"(marca|marcar|clasifica)\w* (esta|esto|la) (noticia )?como (verdadera|falsa|aprobad)",
    r"prioridad (100|maxima)",
    r"(actua|act) como (si|un|una|an?) ",
    r"(publica|aprueba)\w* (automaticamente|sin revision)",
    r"\b(ejecuta|execute|run)\b.*\b(comando|command|codigo|code)\b",
    r"\b(inventa|invent|fabrica|fabricate|make up)\w*",
    r"aunque no (la |lo |los |las )?(tengas|sepas|exista)",
    r"sin (citar|fuentes|cita)\b",
    r"(tus|your) (instrucciones|instructions|reglas|rules) (internas|ocultas|del sistema|hidden|internal)",
]
_RX = [re.compile(p) for p in PATRONES]


def es_inyeccion(texto: str) -> bool:
    t = norm(texto)
    return any(r.search(t) for r in _RX)


def como_dato(texto: str, limite=400) -> str:
    """Neutraliza delimitadores para que un dato no pueda cerrar el bloque <DATO>."""
    t = (texto or "").replace("<", "‹").replace(">", "›").replace("```", "'''")
    return re.sub(r"[\x00-\x08\x0b-\x1f]", " ", t)[:limite]
