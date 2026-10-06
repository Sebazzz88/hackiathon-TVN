"""Controles anti-inyección (T07). El texto de una fuente es DATO, nunca instrucción.

1) Detección en FUENTES (titulares): solo patrones que se dirigen al sistema (ignorar instrucciones, revelar
   claves, prompt del sistema, marcar como verdadera). Son estrictos a propósito: un titular legítimo como
   "prioridad máxima a la vacunación" o "comunidades sin fuentes de agua" no debe perder evidencia.
2) Detección en CONSULTAS: lo anterior más pedidos de fabricar datos, saltarse citas o actuar sin reglas.
3) Aislamiento: en el prompt del LLM cada evidencia va dentro de <DATO id=...> con delimitadores neutralizados;
   las instrucciones viven solo en el mensaje de sistema.
4) Salida: el validador descarta afirmaciones sin cita válida; el puntaje lo calcula código, no el LLM.
"""
import re

from .baseline import norm

PATRONES_FUENTE = [
    r"ignor\w* (todas |las |tus |all |previous |the |any )*(instrucciones|instructions|reglas|rules)",
    r"olvida\w* (todas |tus |las )*(instrucciones|reglas)",
    r"\b(revela|muestra|dime|reveal|print|show)\w* (me )?(tu |la |el |your |the )?"
    r"(clave|api ?key|contrasena|password|secreto|secret|system prompt|prompt del sistema|token)",
    r"\b(system prompt|prompt del sistema|jailbreak|modo desarrollador|developer mode)\b",
    r"\b(marca|marcar|clasifica)\w* (esta|esto|la) (noticia )?como (verdadera|falsa|aprobad)",
    r"(tus|your) (instrucciones|instructions|reglas|rules) (internas|ocultas|del sistema|hidden|internal)",
]
PATRONES_CONSULTA = PATRONES_FUENTE + [
    r"prioridad (de )?100\b",
    r"\b(actua|act) como si\b",
    r"\b(actua|act) como (un|una|an?) \w+ sin (reglas|restricciones|limites)",
    r"\b(publica|aprueba)\w* (automaticamente|sin revision)",
    r"\b(ejecuta|execute|run)\b.*\b(comando|command|codigo|code|script)\b",
    r"\b(inventa|inventate|inventar|invent|make up)\b",
    r"aunque no (la |lo |los |las )?(tengas|sepas|exista|existan)",
    r"\bsin (citar|cita|citas)\b",
]
_RX_F = [re.compile(p) for p in PATRONES_FUENTE]
_RX_Q = [re.compile(p) for p in PATRONES_CONSULTA]


def es_inyeccion(texto: str) -> bool:
    """Para textos de FUENTES (titulares, salidas del LLM)."""
    t = norm(texto)
    return any(r.search(t) for r in _RX_F)


def consulta_maliciosa(texto: str) -> bool:
    """Para CONSULTAS del usuario: incluye pedidos de fabricar datos o saltarse las reglas."""
    t = norm(texto)
    return any(r.search(t) for r in _RX_Q)


def como_dato(texto: str, limite=400) -> str:
    """Neutraliza delimitadores para que un dato no pueda cerrar el bloque <DATO>."""
    t = (texto or "").replace("<", "‹").replace(">", "›").replace("```", "'''")
    return re.sub(r"[\x00-\x08\x0b-\x1f]", " ", t)[:limite]
