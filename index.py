"""Entrada para Vercel: la misma app de FastAPI (backend/app/main.py) como una función de Python.

En Vercel el disco es de solo lectura salvo /tmp: la base de revisiones vive en /tmp (se vuelve a generar desde el
snapshot cuando arranca una instancia nueva) y la IA generativa queda en modo sin red: caché de Hermes o plantilla.
Para presentar con la IA local encendida usa run_demo.ps1; esta copia en línea es el respaldo.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))
os.environ.setdefault("AGENT_MODE", "live")
os.environ.setdefault("LLM_OFFLINE", "1")
os.environ.setdefault("DB_PATH", "/tmp/nexo.db")
os.environ.setdefault("JURADO_ULTIMO", "/tmp/jurado_ultimo.json")

from app.main import app  # noqa: E402,F401
