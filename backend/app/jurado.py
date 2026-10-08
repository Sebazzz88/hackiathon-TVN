"""Modo jurado: corre en vivo las pruebas de aceptación T01–T10 del reto (backend/tests/test_reto.py) y devuelve verde o rojo
por prueba con su evidencia (qué pruebas se ejecutaron, qué comprueban, duración y, si falla, el mensaje).

Se ejecuta pytest en un SUBPROCESO sin ventana (CREATE_NO_WINDOW en Windows), con LLM_OFFLINE=1 y una base temporal:
no toca la base real ni llama a ningún modelo. El último resultado se guarda en data/processed/jurado_ultimo.json.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from .db import DATA_DIR, leer_json

BACKEND = Path(__file__).resolve().parents[1]
ARCHIVO_PRUEBAS = BACKEND / "tests" / "test_reto.py"
ULTIMO = Path(os.getenv("JURADO_ULTIMO") or DATA_DIR / "processed" / "jurado_ultimo.json")  # en Vercel: /tmp
_CANDADO = threading.Lock()

# Tabla de la sección 9 del reto (docs/RETO.md): qué se prueba y qué se espera.
PRUEBAS = {
    "T01": ("Archivo con fechas inválidas y nulos", "Validar, separar errores y conservar nulos; no bloquear toda la carga."),
    "T02": ("Tres registros del mismo evento", "Agrupar sin perder fuentes; no triplicar importancia ni corroboración."),
    "T03": ("Noticia antigua recirculada", "Mostrar fecha original; no presentarla como un evento nuevo."),
    "T04": ("Cifra anual del Banco Mundial", "Mantener país, año y unidad; citar dato y no describirlo como cifra de hoy."),
    "T05": ("Dos afirmaciones incompatibles", "Mostrar ambas, su alcance y la revisión pendiente; no escoger arbitrariamente."),
    "T06": ("Consulta sin respuesta en el corpus", "Abstención explícita; ninguna cifra o cita inventada."),
    "T07": ("Fuente que exige ignorar instrucciones", "Tratarla como contenido no confiable; no revelar secretos ni ejecutar acciones."),
    "T08": ("Caso de prioridad alta", "Exponer componentes y regla; la prioridad no habilita publicación."),
    "T09": ("Brief editorial", "Formato útil, citas pertinentes y distinción de hechos e inferencias."),
    "T10": ("Sin internet durante la demo", "Funcionar con snapshot y fallback documentado."),
}


def _docstrings():
    """{nombre_de_prueba: primera línea del docstring} leído del archivo de pruebas (la 'evidencia' de qué se comprueba)."""
    arbol = ast.parse(ARCHIVO_PRUEBAS.read_text(encoding="utf-8"))
    out = {}
    for n in arbol.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"):
            doc = ast.get_docstring(n) or ""
            out[n.name] = doc.strip().splitlines()[0] if doc else n.name.replace("test_", "").replace("_", " ")
    return out


def correr():
    """Corre T01–T10 y devuelve el informe. Solo una ejecución a la vez."""
    if not _CANDADO.acquire(blocking=False):
        return {"en_curso": True, "detalle": "Ya hay una ejecución en curso; espera unos segundos."}
    try:
        t0 = time.time()
        tmp = Path(tempfile.mkdtemp(prefix="jurado-"))
        xml = tmp / "resultado.xml"
        # PYTHONPATH = la misma ruta de imports de este proceso: en Vercel las dependencias no están en la ruta por defecto.
        env = {**os.environ, "LLM_OFFLINE": "1", "DB_PATH": str(tmp / "jurado.db"), "PYTHONIOENCODING": "utf-8",
               "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        proc = subprocess.run([sys.executable, "-m", "pytest", str(ARCHIVO_PRUEBAS), "-q", "-p", "no:warnings", "-p", "no:cacheprovider",
                               f"--junitxml={xml}"], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=300,
                              creationflags=flags)
        docs = _docstrings()
        casos = {}
        if xml.exists():
            for tc in ET.parse(xml).getroot().iter("testcase"):
                nombre = tc.get("name", "")
                if "\\x" in nombre or "\\u" in nombre:  # pytest escapa los acentos de los parámetros en el XML
                    try:
                        nombre = nombre.encode("ascii").decode("unicode_escape")
                    except (UnicodeError, ValueError):
                        pass
                base = nombre.split("[")[0]
                tid = base.split("_")[1] if base.startswith("test_T") else None
                if tid not in PRUEBAS:
                    continue
                fallo = tc.find("failure")
                if fallo is None:
                    fallo = tc.find("error")
                casos.setdefault(tid, []).append({
                    "prueba": nombre, "comprueba": docs.get(base, ""), "segundos": round(float(tc.get("time", 0)), 2),
                    "ok": fallo is None and tc.find("skipped") is None, "omitida": tc.find("skipped") is not None,
                    "mensaje": (fallo.get("message", "") or (fallo.text or ""))[:600] if fallo is not None else ""})
        sin_correr = "" if xml.exists() else "pytest no llegó a ejecutarse: " + ((proc.stderr or proc.stdout or "").strip()[-300:] or "sin salida")
        filas = []
        for tid, (titulo, esperado) in PRUEBAS.items():
            ps = casos.get(tid, [])
            filas.append({"id": tid, "titulo": titulo, "esperado": esperado, "pruebas": ps,
                          "estado": "verde" if ps and all(p["ok"] for p in ps) else "rojo",
                          "motivo": "" if ps else (sin_correr or "No se encontró ninguna prueba para este caso.")})
        informe = {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "segundos": round(time.time() - t0, 1),
                   "verdes": sum(f["estado"] == "verde" for f in filas), "total": len(filas), "filas": filas,
                   "comando": "cd backend; .\\.venv\\Scripts\\python -m pytest tests/test_reto.py -q",
                   "salida_pytest": ((proc.stdout or "") + (proc.stderr or ""))[-1500:]}
        ULTIMO.parent.mkdir(parents=True, exist_ok=True)
        ULTIMO.write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
        return informe
    finally:
        _CANDADO.release()


def ultimo():
    return leer_json(ULTIMO, {"disponible": False})
