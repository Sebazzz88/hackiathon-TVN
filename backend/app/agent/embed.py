"""Embeddings multilingües LOCALES (fastembed/ONNX, sin internet una vez descargado el modelo).

- Modelo en data/models/ (se descarga una vez con `python -m app.agent.embed --descargar`).
- Caché de vectores en data/processed/embeddings.npz para que la demo no recalcule.
- Respaldo documentado: si el modelo no está disponible, n-gramas de caracteres con hashing (léxico, peor
  calidad semántica). El backend en uso se informa en /api/eval y en cada ficha.
"""
import hashlib
import re
import sys
import unicodedata

import numpy as np

from .config import EMB_MODEL, data_dir

_model = None
BACKEND = "sin_inicializar"
_cache: dict = {}
_cache_dirty = False


def _key(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()


def _cache_path():
    return data_dir() / "processed" / "embeddings.npz"


def _load_cache():
    global _cache
    if _cache:
        return
    p = _cache_path()
    if p.exists():
        z = np.load(p)
        if str(z["modelo"]) == EMB_MODEL:
            _cache = dict(zip(z["keys"].tolist(), z["vecs"]))


def guardar_cache():
    global _cache_dirty
    if not _cache_dirty or BACKEND != "fastembed":
        return
    keys = list(_cache)
    p = _cache_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, keys=np.array(keys), vecs=np.stack([_cache[k] for k in keys]), modelo=np.array(EMB_MODEL))
    _cache_dirty = False


def _get_model():
    global _model, BACKEND
    if _model is not None or BACKEND == "hash":
        return _model
    try:
        from fastembed import TextEmbedding
        _model = TextEmbedding(EMB_MODEL, cache_dir=str(data_dir() / "models"), local_files_only=True)
        BACKEND = "fastembed"
    except Exception as e:  # modelo no descargado o sin internet: respaldo léxico
        print(f"[embed] modelo local no disponible ({type(e).__name__}); uso respaldo por n-gramas", file=sys.stderr)
        BACKEND = "hash"
    return _model


def _norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in t if not unicodedata.combining(c)))


def _hash_vec(t, dim=1024):
    v = np.zeros(dim, dtype=np.float32)
    s = f"  {_norm(t)}  "
    for n in (3, 4):
        for i in range(len(s) - n + 1):
            v[int(hashlib.md5(s[i:i + n].encode()).hexdigest()[:8], 16) % dim] += 1
    return v


def embed(textos) -> np.ndarray:
    """Devuelve matriz (n, d) normalizada L2."""
    global _cache_dirty
    textos = list(textos)
    if not textos:
        return np.zeros((0, 384), dtype=np.float32)
    m = _get_model()
    if m is None:
        X = np.stack([_hash_vec(t) for t in textos])
    else:
        _load_cache()
        falt = [t for t in dict.fromkeys(textos) if _key(t) not in _cache]
        if falt:
            for t, v in zip(falt, m.embed(falt, batch_size=64)):
                _cache[_key(t)] = np.asarray(v, dtype=np.float32)
            _cache_dirty = True
        X = np.stack([_cache[_key(t)] for t in textos])
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.where(n == 0, 1, n)


def descargar():
    from fastembed import TextEmbedding
    TextEmbedding(EMB_MODEL, cache_dir=str(data_dir() / "models"))
    print("Modelo listo en", data_dir() / "models")


if __name__ == "__main__":
    if "--descargar" in sys.argv:
        descargar()
