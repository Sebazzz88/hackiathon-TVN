#!/usr/bin/env python3
"""Regenera TODAS las páginas generadas de Notion (05, 10, 11 y 12) desde el sistema. Atajo de:
    cd backend; .\\.venv\\Scripts\\python -m app.notion_export [--correr]
Uso (desde la raíz del repo):  backend\\.venv\\Scripts\\python docs\\notion_export\\generar_fichas.py [--correr]
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
os.environ["LLM_OFFLINE"] = "1"  # sin red y reproducible (caché o plantilla)

from app import notion_export  # noqa: E402

if __name__ == "__main__":
    for ruta in notion_export.exportar(correr="--correr" in sys.argv).values():
        print("escrito", ruta)
