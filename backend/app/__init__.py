"""Carga mínima de .env (raíz del repo o backend/) sin dependencias. No sobrescribe variables ya definidas
y nunca imprime valores (las credenciales no deben aparecer en logs)."""
import os
from pathlib import Path


def _cargar_env():
    raiz = Path(__file__).resolve().parents[2]
    for p in (raiz / ".env", raiz / "backend" / ".env"):
        if not p.exists():
            continue
        for linea in p.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            v = v.split(" #")[0].strip().strip('"').strip("'")
            if v:
                os.environ.setdefault(k.strip(), v)


_cargar_env()
