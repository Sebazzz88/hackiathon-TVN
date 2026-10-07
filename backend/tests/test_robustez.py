"""Robustez de la demo (punto 7): sin internet y con la IA caída, el sistema sigue: caché → plantilla/extractiva →
abstención clara. Nunca un error 500 en consulta o borrador. Y ninguna credencial en el repositorio."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

os.environ["LLM_OFFLINE"] = "1"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import agent as agente_live  # noqa: E402
from app import db, main, scoring  # noqa: E402
from app.agent import draft, llm, pipeline  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


def _red_caida(*a, **k):
    raise httpx.ConnectError("sin red (simulado)")


@pytest.fixture
def ia_caida(monkeypatch):
    """El proveedor parece disponible pero toda llamada de red falla (Ollama se cae a mitad de la demo)."""
    monkeypatch.setenv("LLM_OFFLINE", "0")
    monkeypatch.setenv("LLM_CACHE_DIR", tempfile.mkdtemp(prefix="cache-llm-"))
    monkeypatch.setattr(llm, "disponible", lambda: (True, ""))
    monkeypatch.setattr(llm.httpx, "post", _red_caida)


@pytest.fixture(scope="module")
def cliente():
    mp = pytest.MonkeyPatch()
    mp.setattr(db, "DB_PATH", os.path.join(tempfile.mkdtemp(), "robustez.db"))
    mp.setattr(main.agent, "AGENT_MODE", "live")
    mp.setattr(main.agent, "answer_query", agente_live.answer_query)
    mp.setattr(main.agent, "generate_draft", agente_live.generate_draft)
    db.init()
    db.replace_all([scoring.aplicar(f) for f in pipeline.seleccionar(pipeline.analizar()["fichas"])])
    db.set_meta("agent_mode", "live")
    db.set_meta("fichas_version", main.FICHAS_VERSION)
    with TestClient(main.app, raise_server_exceptions=False) as c:
        yield c
    mp.undo()


def _ficha_con_evidencia():
    return next(f for f in pipeline.analizar()["fichas"] if not f.sintetico and f.estado_evidencia != "insuficiente")


def test_ia_caida_devuelve_none_sin_excepcion(ia_caida):
    salida, meta = llm.generar_json("s", "u", {"type": "object"}, "v-prueba")
    assert salida is None and meta["origen"] == "sin_llm" and "ConnectError" in meta["motivo"]


def test_la_cache_responde_aunque_la_ia_este_caida(ia_caida):
    key = llm.cache_key("s", "u", {"type": "object"}, "v-prueba")
    llm.cache_dir().mkdir(parents=True, exist_ok=True)
    (llm.cache_dir() / f"{key}.json").write_text(json.dumps({"meta": {"modelo": "x"}, "salida": {"ok": 1}}), encoding="utf-8")
    salida, meta = llm.generar_json("s", "u", {"type": "object"}, "v-prueba")
    assert salida == {"ok": 1} and meta["origen"] == "cache"


def test_cache_danada_no_rompe(ia_caida):
    key = llm.cache_key("s", "u2", {"type": "object"}, "v-prueba")
    llm.cache_dir().mkdir(parents=True, exist_ok=True)
    (llm.cache_dir() / f"{key}.json").write_text("{no es json", encoding="utf-8")
    salida, meta = llm.generar_json("s", "u2", {"type": "object"}, "v-prueba")
    assert salida is None and meta["origen"] == "sin_llm"


def test_borrador_con_ia_caida_usa_plantilla_validada(ia_caida):
    b = draft.generar(_ficha_con_evidencia())
    assert b["generador"] == "plantilla_determinista"
    assert b["afirmaciones"] and all(a["citas"] for a in b["afirmaciones"])


def test_consulta_con_ia_caida_responde_200(cliente, ia_caida):
    r = cliente.post("/api/query", json={"pregunta": "¿Qué pasa con S&P y la calificación de Panamá?", "ia": True})
    assert r.status_code == 200
    assert r.json()["estado"] in ("respondida", "abstencion", "contradiccion")


def test_consulta_que_revienta_termina_en_abstencion_clara(cliente, monkeypatch):
    def revienta(*a, **k):
        raise RuntimeError("fallo interno simulado")
    monkeypatch.setattr(main.agent, "answer_query", revienta)
    r = cliente.post("/api/query", json={"pregunta": "cualquier cosa"})
    assert r.status_code == 200
    d = r.json()
    assert d["estado"] == "abstencion" and d["faltante"] and d["accion"]
    assert "fallo interno simulado" not in json.dumps(d)  # el detalle va al log, no a la pantalla


def test_borrador_que_revienta_termina_en_abstencion_clara(cliente, monkeypatch):
    def revienta(*a, **k):
        raise RuntimeError("fallo interno simulado")
    monkeypatch.setattr(main.agent, "generate_draft", revienta)
    fid = _ficha_con_evidencia().id_caso
    r = cliente.post(f"/api/fichas/{fid}/draft")
    assert r.status_code == 200
    b = r.json()["borrador"]
    assert b["abstencion"] and "Reintenta" in b["faltante"][0]


def test_no_hay_credenciales_en_el_repositorio():
    """Ningún archivo versionado contiene una clave de API; .env no se versiona."""
    try:
        archivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split("\n")
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git no disponible")
    assert ".env" not in archivos
    patrones = [re.compile(p) for p in (r"sk-ant-[A-Za-z0-9_-]{20,}", r"\bsk-[A-Za-z0-9]{32,}", r"AKIA[0-9A-Z]{16}",
                                        r"gh[pousr]_[A-Za-z0-9]{30,}", r"AIza[0-9A-Za-z_-]{35}",
                                        r"(?m)^\s*(LLM_API_KEY|ANTHROPIC_API_KEY)\s*=\s*\S{8,}")]
    hallazgos = []
    for a in filter(None, archivos):
        p = RAIZ / a
        if p.suffix.lower() in {".pdf", ".png", ".jpg", ".npz", ".onnx", ".db", ".ico"} or not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        texto = p.read_text(encoding="utf-8", errors="ignore")
        hallazgos += [f"{a}: {r.pattern}" for r in patrones if r.search(texto)]
    assert not hallazgos, hallazgos


def test_un_solo_proceso_sirve_interfaz_y_api(cliente):
    """run_demo.ps1 / Docker: el backend sirve la interfaz compilada en "/" sin tapar /api ni /health."""
    if not (RAIZ / "frontend" / "dist" / "index.html").exists():
        pytest.skip("interfaz sin compilar (npm run build)")
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert cliente.get("/health").json()["ok"] is True
    assert cliente.get("/api/inbox?limit=5").status_code == 200
