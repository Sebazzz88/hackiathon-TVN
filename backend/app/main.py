import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from fastapi.responses import JSONResponse, PlainTextResponse

from . import db, scoring, agent_interface as agent
from .models import Bandeja, BandejaItem, Ficha, QueryIn, QueryOut, ReviewIn

log = logging.getLogger("copiloto")
MAX_BANDEJA = 1000  # "Máx" en la interfaz pide todo; el snapshot tiene ~720 temas


FICHAS_VERSION = "4"  # súbela al cambiar los campos de las fichas: se regeneran sin perder revisiones ni borradores


def sembrar(conservar=True):
    """Genera las fichas fuera de la base y las guarda en una sola transacción (nadie ve la tabla a medias).
    conservar=True mantiene el trabajo humano (estado, revisiones y borrador) de las fichas que siguen existiendo."""
    nuevas = [scoring.aplicar(f) for f in agent.build_candidates()]
    if conservar:
        viejas = {d["id_caso"]: d for d in db.all_fichas()}
        for f in nuevas:
            v = viejas.get(f.id_caso)
            if v:
                f.estado_revision, f.revisiones, f.borrador = v.get("estado_revision", "nuevo"), v.get("revisiones", []), v.get("borrador")
    db.replace_all(nuevas)
    db.set_meta("agent_mode", agent.AGENT_MODE)
    db.set_meta("fichas_version", FICHAS_VERSION)


@asynccontextmanager
async def lifespan(_):
    db.init()
    if db.count() == 0 or db.get_meta("agent_mode") != agent.AGENT_MODE or db.get_meta("fichas_version") != FICHAS_VERSION:
        sembrar()  # re-siembra si cambió el modo (stub <-> live); las revisiones previas quedan en audit
    if agent.AGENT_MODE == "live":  # carga el modelo local (Ollama) en memoria sin bloquear el arranque
        import threading
        from .agent import llm
        threading.Thread(target=llm.precargar, daemon=True).start()
    yield


app = FastAPI(title="Nexo · Copiloto editorial – De la señal a la decisión", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def error_inesperado(request, exc):
    """Nunca una pantalla de error cruda: siempre JSON con un mensaje que dice qué hacer. El detalle va al log."""
    log.exception("Error en %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={
        "detail": "El servidor tuvo un problema al procesar la solicitud. Reintenta; si persiste, revisa la ventana del backend."})


def _ficha(id_caso) -> Ficha:
    d = db.get(id_caso)
    if not d:
        raise HTTPException(404, "Ficha no encontrada")
    return Ficha(**d)


@app.get("/health")
def health():
    return {"ok": True, "agent_mode": agent.AGENT_MODE, "reglas": scoring.VERSION, "pesos": scoring.PESOS}


@app.get("/api/meta")
def meta():
    """Resumen del snapshot para la interfaz: fecha de corte, archivos con SHA-256 y cobertura."""
    p = db.DATA_DIR / "raw" / "manifest.json"
    m = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return {"version": m.get("version"), "fecha_corte_UTC": m.get("fecha_corte_UTC"), "archivos": m.get("archivos", {}),
            "consultas": len(m.get("consultas", [])), "consultas_fallidas": len(m.get("consultas_fallidas", [])),
            "licencia_condiciones": m.get("licencia_condiciones"), "nota_intervalo": m.get("nota_intervalo"),
            "fichas": db.count(), "agent_mode": agent.AGENT_MODE, "ia": _estado_ia()}


_IA_CACHE = {"t": 0.0, "v": None}


def _estado_ia():
    """Estado de la IA con caché de 10 s: comprobar Ollama en cada petición sería lento e innecesario."""
    import time
    if agent.AGENT_MODE != "live":
        return {"conectado": False, "modo": "stub"}
    if _IA_CACHE["v"] is None or time.time() - _IA_CACHE["t"] > 10:
        from .agent import embed, llm
        _IA_CACHE.update(t=time.time(), v={**llm.estado(), "embeddings": "multilingües locales (ONNX)" if embed.BACKEND != "hash" else "respaldo léxico"})
    return _IA_CACHE["v"]


@app.get("/api/quality-report")
def quality_report():
    p = db.DATA_DIR / "processed" / "quality_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"disponible": False}


@app.get("/api/inbox", response_model=Bandeja)
def inbox(limit: int = 5, sinteticos: bool = False, tema: str | None = None, dias: int | None = None):
    """Bandeja priorizada: solo las `limit` fichas pedidas (máx. 1000), traídas con una consulta SQL. Por defecto solo
    reales; sinteticos=true lista los casos controlados de prueba. En modo stub (datos DEMO) no se filtra."""
    limit = max(1, min(limit, MAX_BANDEJA))
    desde = None
    if dias:
        from datetime import timedelta
        from .agent.corpus import fecha_corte
        desde = (fecha_corte() - timedelta(days=max(1, min(dias, 90)))).isoformat(timespec="minutes")
    total, filas = db.inbox(limit, sinteticos if agent.AGENT_MODE == "live" else None, tema or None, desde)
    items = []
    for d in filas:
        try:
            items.append(BandejaItem(**d))
        except Exception:  # una ficha corrupta no debe tumbar la agenda entera
            log.warning("Ficha omitida de la bandeja por datos inválidos: %s", d.get("id_caso"))
    return Bandeja(total=total, limit=limit, items=items)


@app.get("/api/fichas/{id_caso}", response_model=Ficha)
def get_ficha(id_caso: str):
    return _ficha(id_caso)


@app.post("/api/query", response_model=QueryOut)
def query(q: QueryIn):
    try:
        out = agent.answer_query(q.pregunta, q.ia)
    except Exception:  # red de seguridad de la demo: nunca una pantalla de error, siempre una abstención que dice qué hacer
        log.exception("La consulta falló; se responde con abstención")
        out = QueryOut(abstencion=True, estado="abstencion", metodo="respaldo",
                       faltante=["El agente no pudo completar esta consulta (el detalle quedó en el log del backend)."],
                       accion="Reintenta la consulta. Mientras tanto, la agenda y las fichas siguen disponibles: no dependen de la IA.")
    db.log("query", "", f"abstencion={out.abstencion}")  # no se registra el texto completo
    if out.validador:
        db.log("validador", "", json.dumps(out.validador))
    return out


@app.post("/api/fichas/{id_caso}/draft", response_model=Ficha)
def draft(id_caso: str):
    f = _ficha(id_caso)
    try:
        f.borrador = agent.generate_draft(f)
    except Exception:  # misma red de seguridad: se informa con una abstención, no con un error 500
        log.exception("El borrador de %s falló; se responde con abstención", id_caso)
        return f.model_copy(update={"borrador": {
            "generador": "ninguno", "abstencion": True, "citas": [],
            "faltante": ["No se pudo generar el borrador (el detalle quedó en el log del backend). Reintenta con «Regenerar»; "
                         "la ficha, sus fuentes y su evidencia siguen disponibles."]}})
    if f.estado_revision == "nuevo":
        f.estado_revision = "en_revision"
    db.save(f)
    db.log("draft", id_caso, (f.borrador or {}).get("generador", ""))
    if (f.borrador or {}).get("validador"):
        db.log("validador", id_caso, json.dumps(f.borrador["validador"]))
    return f


@app.post("/api/fichas/{id_caso}/review", response_model=Ficha)
def review(id_caso: str, r: ReviewIn):
    f = _ficha(id_caso)
    if r.estado == "aprobado_como_borrador":
        if f.estado_evidencia == "insuficiente":
            raise HTTPException(409, "Evidencia insuficiente: no se puede aprobar. Requiere investigación.")
        if not f.borrador:
            raise HTTPException(409, "Genera el borrador antes de aprobarlo.")
    f.estado_revision = r.estado
    f.revisiones = f.revisiones + [{"estado": r.estado, "revisor": r.revisor, "comentario": r.comentario,
                                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}]
    db.save(f)
    db.log("review", id_caso, f"{r.estado} por {r.revisor}: {r.comentario}")
    return f


@app.get("/api/validador")
def validador():
    """Cuántas afirmaciones ha revisado el validador y cuántas eliminó (acumulado, desde el registro de auditoría)."""
    return db.validador_totales()


@app.get("/api/evidencia/{id_ev:path}")
def evidencia(id_ev: str):
    """Registro FUENTE de una cita (titular, medio, fechas, URL; o indicador, país, año, unidad), para abrirlo desde la UI."""
    from .agent import corpus
    r = corpus.registro_publico(id_ev)
    if not r:
        raise HTTPException(404, f"La evidencia «{id_ev}» no existe en el corpus.")
    return r


@app.get("/api/audit")
def audit():
    return db.audit()


@app.get("/api/export/fichas.jsonl", response_class=PlainTextResponse)
def export_fichas():
    """fichas.jsonl con el estado actual (incluye borrador y revisión) para registrar en Notion."""
    return "\n".join(json.dumps(d, ensure_ascii=False) for d in db.all_fichas())


@app.get("/api/jurado/pruebas")
def jurado_ultimo():
    """Último resultado de T01–T10 (sin volver a correrlas)."""
    from . import jurado
    return jurado.ultimo()


@app.post("/api/jurado/pruebas")
def jurado_correr():
    """Corre T01–T10 en vivo (subproceso sin ventana, ~10 s) y devuelve verde/rojo por prueba con su evidencia."""
    from . import jurado
    return jurado.correr()


@app.get("/api/jurado/metricas")
def jurado_metricas():
    """Tabla agente vs baseline leída de eval/results.json (la escribe eval/run_eval.py; nada se escribe a mano)."""
    p = db.ROOT / "eval" / "results.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"disponible": False,
            "detalle": "Falta eval/results.json: corre backend\\.venv\\Scripts\\python eval\\run_eval.py"}


@app.get("/api/eval")
def eval_report():
    p = db.ROOT / "eval" / "resultados" / "resumen.json"
    info = {}
    if agent.AGENT_MODE == "live":
        from .agent import pipeline
        info = pipeline.info()
    return {"agente": info, "evaluacion": json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"disponible": False}}


@app.post("/api/reset")
def reset():
    """Vuelve a generar las fichas desde el snapshot (borra estados de revisión; el audit se conserva)."""
    sembrar(conservar=False)
    db.log("reset")
    return {"ok": True, "fichas": db.count()}


# Demo en un solo proceso: si existe la interfaz compilada (frontend/dist), el backend la sirve en "/" (run_demo.ps1, Docker).
# Se monta al final para que /api y /health tengan prioridad. Con "npm run dev" (puerto 5173) esto no interviene.
def _montar_interfaz():
    import os
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles
    dist = Path(os.getenv("FRONTEND_DIST") or db.ROOT / "frontend" / "dist")
    if (dist / "index.html").exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="interfaz")


_montar_interfaz()
