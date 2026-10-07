"""PUNTO DE CONEXIÓN CON LA IA (Persona 1).

El backend SOLO llama a estas 3 funciones. En AGENT_MODE=stub devuelven datos demo
marcados como sintéticos. En AGENT_MODE=live se importan desde backend/app/agent/__init__.py
(créalo tú) con las MISMAS firmas. Ver NOTA_PERSONA_1.md.
"""
import os
from .models import Ficha, Componentes, QueryOut, Cita

AGENT_MODE = os.getenv("AGENT_MODE", "stub")


def build_candidates() -> list[Ficha]:
    """Agrupa noticias, contextualiza y devuelve fichas con componentes R,I,U,N,E (0-1).
    El backend calcula puntaje/banda/orden (scoring.py)."""
    demo = [
        ("DEMO-001", "[DEMO] Tema con evidencia parcial", (0.9, 0.7, 0.8, 0.6, 0.5), "parcial"),
        ("DEMO-002", "[DEMO] Tema prioritario sin evidencia", (0.95, 0.9, 0.9, 0.8, 0.1), "insuficiente"),
        ("DEMO-003", "[DEMO] Tema de menor atención", (0.4, 0.3, 0.2, 0.5, 0.7), "suficiente_para_borrador"),
    ]
    return [
        Ficha(id_caso=i, titulo=t, ids_fuente=[f"{i}-S1"], componentes=Componentes(R=c[0], I=c[1], U=c[2], N=c[3], E=c[4]),
              estado_evidencia=e, faltante=["Fuente primaria (dato sintético de ejemplo)"] if e != "suficiente_para_borrador" else [],
              sintetico=True)
        for i, t, c, e in demo
    ]


def answer_query(pregunta: str, ia: bool = False) -> QueryOut:
    """Responde SOLO con evidencia recuperada; si no hay, abstencion=True y explica qué falta."""
    return QueryOut(abstencion=True, faltante=["Agente en modo stub: sin corpus conectado"])


def generate_draft(ficha: Ficha) -> dict:
    """Brief (<=250 palabras), título, enfoque, 3 preguntas, guion 45-60 s, copy <=80 palabras. Citas por afirmación."""
    return {"stub": True, "brief": "[STUB] Borrador no generado: agente no conectado.", "preguntas": [], "guion": "", "copy": "", "citas": []}


if AGENT_MODE == "live":
    from app.agent import answer_query, build_candidates, generate_draft  # noqa: F811
