"""Cliente LLM (Claude, SDK oficial de Anthropic) con caché en disco para la demo sin internet (T10).

- Clave: LLM_API_KEY (o ANTHROPIC_API_KEY) en .env. Nunca en código, prompts ni logs.
- Modelo: LLM_MODEL (por defecto claude-opus-5-5). Esfuerzo: LLM_EFFORT (por defecto low, para latencia).
- Salida JSON obligatoria vía output_config.format (json_schema).
- Caché: data/cache/llm/<sha256>.json, clave = modelo + versión de prompt + mensajes. Se versiona en git para
  que la demo funcione offline con los borradores ya generados.
- Si no hay clave, no hay red o la llamada falla: devuelve None y el borrador usa la plantilla determinista.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from .config import data_dir

PRECIOS = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-4-5": (1.0, 5.0),
           "claude-fable-5-1": (10.0, 50.0)}  # USD por millón de tokens (entrada, salida)


def modelo():
    return os.getenv("LLM_MODEL") or "claude-opus-5-5"


def _clave():
    return os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or ""


def cache_dir():
    d = os.getenv("LLM_CACHE_DIR")
    return Path(d) if d else data_dir() / "cache" / "llm"


def _ruta(key):
    return cache_dir() / f"{key}.json"


def cache_key(system, user, schema, version):
    raw = json.dumps([modelo(), version, system, user, schema], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def generar_json(system: str, user: str, schema: dict, version: str):
    """Devuelve (dict|None, meta). meta incluye origen: cache | llm | sin_llm, tokens, costo y segundos."""
    key = cache_key(system, user, schema, version)
    p = _ruta(key)
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return d["salida"], {**d["meta"], "origen": "cache", "cache_key": key}
    if not _clave() or os.getenv("LLM_OFFLINE") == "1":
        return None, {"origen": "sin_llm", "motivo": "sin clave LLM o modo offline", "cache_key": key}
    t0 = time.time()
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=_clave(), timeout=60.0, max_retries=1)
        r = client.messages.create(
            model=modelo(), max_tokens=8000, system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": os.getenv("LLM_EFFORT", "low"),
                           "format": {"type": "json_schema", "schema": schema}},
        )
        if r.stop_reason == "refusal":
            return None, {"origen": "sin_llm", "motivo": "el modelo declinó la solicitud", "cache_key": key}
        texto = next(b.text for b in r.content if b.type == "text")
        salida = json.loads(texto)
    except Exception as e:  # sin red, clave inválida, límite, JSON inválido: se usa la plantilla
        print(f"[llm] fallo {type(e).__name__}; se usa plantilla determinista", file=sys.stderr)
        return None, {"origen": "sin_llm", "motivo": f"error {type(e).__name__}", "cache_key": key}
    pin, pout = PRECIOS.get(modelo(), (0, 0))
    meta = {"modelo": modelo(), "tokens_entrada": r.usage.input_tokens, "tokens_salida": r.usage.output_tokens,
            "costo_usd": round((r.usage.input_tokens * pin + r.usage.output_tokens * pout) / 1e6, 5),
            "segundos": round(time.time() - t0, 2), "prompt_version": version}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"meta": meta, "salida": salida}, ensure_ascii=False, indent=1), encoding="utf-8")
    return salida, {**meta, "origen": "llm", "cache_key": key}


def estado() -> dict:
    """Estado de la IA generativa para la interfaz. Nunca expone la clave."""
    clave, offline = bool(_clave()), os.getenv("LLM_OFFLINE") == "1"
    d = cache_dir()
    return {"modelo": modelo(), "clave_configurada": clave, "offline": offline, "conectado": clave and not offline,
            "respuestas_en_cache": len(list(d.glob("*.json"))) if d.exists() else 0}
