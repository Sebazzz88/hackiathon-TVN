"""Configuración del agente. Sin secretos: la clave del LLM solo se lee de variables de entorno (.env)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    d = os.getenv("DATA_DIR")
    if not d:
        return ROOT / "data"
    p = Path(d)
    if not p.is_absolute():  # relativo a backend/ (como en .env.example) o al cwd
        cand = (ROOT / "backend" / p).resolve()
        p = cand if cand.exists() else p.resolve()
    return p


AGENT_VERSION = "agente-v1"
EMB_MODEL = os.getenv("EMB_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Umbrales calibrados sobre el snapshot (ver docs/04_AGENT.md)
SIM_CLUSTER = float(os.getenv("SIM_CLUSTER", "0.80"))     # mismo evento
SIM_QUERY_MIN = float(os.getenv("SIM_QUERY_MIN", "0.45"))  # por debajo: abstención
VENTANA_EVENTO_H = 120                                      # registros a >5 días no se agrupan
VIDA_MEDIA_URGENCIA_H = 48
DIAS_RECIRCULADA = 30

TEMAS = {
    "economia": "Economía",
    "logistica_canal": "Logística / Canal",
    "turismo": "Turismo",
    "servicios_publicos": "Servicios públicos",
    "eventos_naturales": "Eventos naturales",
    "regulacion": "Regulación",
    "otros": "Fuera de los 6 temas",
}

LEYENDA = "Basado únicamente en titular/metadatos. No se leyó el artículo completo."
