"""Agente IA del Copiloto TVN (AGENT_MODE=live). Mismas firmas que app/agent_interface.py."""
from ..models import Ficha, QueryOut


def build_candidates() -> list[Ficha]:
    from . import pipeline
    fichas = pipeline.seleccionar(pipeline.analizar()["fichas"])
    pipeline.exportar_jsonl(fichas)
    return fichas


def answer_query(pregunta: str, ia: bool = False) -> QueryOut:
    from .query import responder
    return responder(pregunta, ia=ia)


def generate_draft(ficha: Ficha) -> dict:
    from .draft import generar
    return generar(ficha)
