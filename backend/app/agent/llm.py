"""Cliente de IA generativa, independiente del proveedor, con caché en disco para la demo sin internet (T10).

Proveedores (LLM_PROVIDER):
  - ollama    (por defecto): modelo LOCAL y gratuito vía Ollama (http://localhost:11434). Sin clave ni internet.
                Salida JSON forzada con el esquema (`format`). Modelo: LLM_MODEL (por defecto hermes3:3b, Nous Research).
  - openai    : cualquier API compatible con OpenAI (Kimi/Moonshot, Groq, OpenRouter…). Requiere LLM_BASE_URL
                y LLM_API_KEY.
  - anthropic : Claude con el SDK oficial. Requiere LLM_API_KEY.
La clave (si aplica) solo se lee de .env; nunca va en código, prompts ni logs.
Caché: data/cache/llm/<sha256>.json (clave = proveedor + modelo + versión de prompt + mensajes). Se versiona para que
la demo funcione offline. Si el proveedor no está disponible o falla, devuelve None y se usa la plantilla determinista.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx

from .config import data_dir

PRECIOS = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0),
           "claude-fable-5-1": (10.0, 50.0)}  # USD por millón de tokens; modelos locales = 0
MODELO_POR_DEFECTO = {"ollama": "hermes3:3b", "anthropic": "claude-opus-5-5", "openai": "moonshot-v1-8k"}


def proveedor():
    return (os.getenv("LLM_PROVIDER") or "ollama").strip().lower()


def modelo():
    return os.getenv("LLM_MODEL") or MODELO_POR_DEFECTO.get(proveedor(), "")


def _clave():
    return os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""


def _ollama_url():
    return (os.getenv("OLLAMA_URL") or "http://localhost:11434").rstrip("/")


def cache_dir():
    d = os.getenv("LLM_CACHE_DIR")
    return Path(d) if d else data_dir() / "cache" / "llm"


def _ruta(key):
    return cache_dir() / f"{key}.json"


def cache_key(system, user, schema, version):
    raw = json.dumps([proveedor(), modelo(), version, system, user, schema], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


# ------------------------------------------------------------------ proveedores
def _ollama(system, user, schema, max_tokens=None):
    """Ollama /api/chat con salida estructurada por esquema. Temperatura 0 para reproducibilidad."""
    r = httpx.post(f"{_ollama_url()}/api/chat", timeout=float(os.getenv("LLM_TIMEOUT", "600")), json={
        "model": modelo(), "stream": False, "format": schema, "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m"),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0, "num_ctx": int(os.getenv("LLM_NUM_CTX", "4096")),
                    **({"num_predict": max_tokens} if max_tokens else {})},
    })
    r.raise_for_status()
    d = r.json()
    return d["message"]["content"], d.get("prompt_eval_count", 0), d.get("eval_count", 0)


def _openai_compatible(system, user, schema, max_tokens=None):
    base = (os.getenv("LLM_BASE_URL") or "").rstrip("/")
    if not base:
        raise RuntimeError("falta LLM_BASE_URL")
    system = system + "\nResponde SOLO con un objeto JSON que cumpla este esquema: " + json.dumps(schema, ensure_ascii=False)
    r = httpx.post(f"{base}/chat/completions", timeout=120.0, headers={"Authorization": f"Bearer {_clave()}"}, json={
        "model": modelo(), "temperature": 0, "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    })
    r.raise_for_status()
    d = r.json()
    u = d.get("usage", {})
    return d["choices"][0]["message"]["content"], u.get("prompt_tokens", 0), u.get("completion_tokens", 0)


def _anthropic(system, user, schema, max_tokens=None):
    import anthropic
    client = anthropic.Anthropic(api_key=_clave(), timeout=60.0, max_retries=1)
    r = client.messages.create(
        model=modelo(), max_tokens=8000, system=system, messages=[{"role": "user", "content": user}],
        output_config={"effort": os.getenv("LLM_EFFORT", "low"), "format": {"type": "json_schema", "schema": schema}},
    )
    if r.stop_reason == "refusal":
        raise RuntimeError("el modelo declinó la solicitud")
    return next(b.text for b in r.content if b.type == "text"), r.usage.input_tokens, r.usage.output_tokens


LLAMADAS = {"ollama": _ollama, "openai": _openai_compatible, "anthropic": _anthropic}


def disponible():
    """(bool, motivo). Para Ollama comprueba que el servidor responda y el modelo esté descargado."""
    if os.getenv("LLM_OFFLINE") == "1":
        return False, "modo offline (LLM_OFFLINE=1)"
    p = proveedor()
    if p not in LLAMADAS:
        return False, f"proveedor desconocido: {p}"
    if p == "ollama":
        try:
            tags = httpx.get(f"{_ollama_url()}/api/tags", timeout=2.0).json().get("models", [])
        except Exception:
            return False, "Ollama no está encendido"
        nombres = {m.get("name") for m in tags} | {m.get("model") for m in tags}
        if modelo() not in nombres and f"{modelo()}:latest" not in nombres:
            return False, f"falta el modelo: ollama pull {modelo()}"
        return True, ""
    if not _clave():
        return False, "falta LLM_API_KEY en .env"
    return True, ""


def generar_json(system: str, user: str, schema: dict, version: str, max_tokens=None, solo_cache=False):
    """Devuelve (dict|None, meta). meta incluye origen: cache | llm | sin_llm, tokens, costo y segundos."""
    key = cache_key(system, user, schema, version)
    p = _ruta(key)
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return d["salida"], {**d["meta"], "origen": "cache", "cache_key": key}
    if solo_cache:
        return None, {"origen": "sin_llm", "motivo": "no solicitado (sin respuesta en caché)", "cache_key": key}
    ok, motivo = disponible()
    if not ok:
        return None, {"origen": "sin_llm", "motivo": motivo, "cache_key": key}
    t0 = time.time()
    try:
        texto, tin, tout = LLAMADAS[proveedor()](system, user, schema, max_tokens)
        salida = json.loads(texto)
        if not isinstance(salida, dict):
            raise ValueError("la salida no es un objeto JSON")
    except Exception as e:  # sin red, modelo caído, JSON inválido: se usa la plantilla
        print(f"[llm] fallo {type(e).__name__}; se usa la plantilla determinista", file=sys.stderr)
        return None, {"origen": "sin_llm", "motivo": f"error {type(e).__name__}", "cache_key": key}
    pin, pout = PRECIOS.get(modelo(), (0, 0))
    meta = {"proveedor": proveedor(), "modelo": modelo(), "tokens_entrada": tin, "tokens_salida": tout,
            "costo_usd": round((tin * pin + tout * pout) / 1e6, 5), "segundos": round(time.time() - t0, 2),
            "prompt_version": version}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"meta": meta, "salida": salida}, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida, {**meta, "origen": "llm", "cache_key": key}


def estado() -> dict:
    """Estado de la IA generativa para la interfaz. Nunca expone la clave."""
    ok, motivo = disponible()
    d = cache_dir()
    return {"proveedor": proveedor(), "modelo": modelo(), "local": proveedor() == "ollama", "conectado": ok,
            "motivo": motivo, "respuestas_en_cache": len(list(d.glob("*.json"))) if d.exists() else 0}


def precargar():
    """Carga el modelo local en memoria (Ollama) para que la primera consulta de la demo no espere la carga."""
    if proveedor() != "ollama" or not disponible()[0]:
        return False
    try:
        httpx.post(f"{_ollama_url()}/api/generate", timeout=120.0,
                   json={"model": modelo(), "prompt": "", "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m")})
        return True
    except Exception:
        return False
