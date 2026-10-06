import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from . import db, scoring, agent_interface as agent
from .models import Ficha, QueryIn, QueryOut, ReviewIn


def sembrar():
    db.clear()
    for f in agent.build_candidates():
        db.save(scoring.aplicar(f))
    db.set_meta("agent_mode", agent.AGENT_MODE)


@asynccontextmanager
async def lifespan(_):
    db.init()
    if not db.all_fichas() or db.get_meta("agent_mode") != agent.AGENT_MODE:
        sembrar()  # re-siembra si cambió el modo (stub <-> live); las revisiones previas quedan en audit
    yield


app = FastAPI(title="Copiloto TVN – De la señal a la decisión", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


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
            "fichas": len(db.all_fichas()), "agent_mode": agent.AGENT_MODE}


@app.get("/api/quality-report")
def quality_report():
    p = db.DATA_DIR / "processed" / "quality_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"disponible": False}


@app.get("/api/inbox", response_model=list[Ficha])
def inbox(limit: int = 5, sinteticos: bool = False):
    """Bandeja priorizada. Por defecto excluye los casos controlados sintéticos (se listan con sinteticos=true)."""
    fs = sorted((Ficha(**d) for d in db.all_fichas()), key=scoring.clave_orden)
    fs = [f for f in fs if f.sintetico == sinteticos] if agent.AGENT_MODE == "live" else fs
    return fs[: max(1, min(limit, 100))]


@app.get("/api/fichas/{id_caso}", response_model=Ficha)
def get_ficha(id_caso: str):
    return _ficha(id_caso)


@app.post("/api/query", response_model=QueryOut)
def query(q: QueryIn):
    out = agent.answer_query(q.pregunta)
    db.log("query", "", f"abstencion={out.abstencion}")  # no se registra el texto completo
    return out


@app.post("/api/fichas/{id_caso}/draft", response_model=Ficha)
def draft(id_caso: str):
    f = _ficha(id_caso)
    f.borrador = agent.generate_draft(f)
    if f.estado_revision == "nuevo":
        f.estado_revision = "en_revision"
    db.save(f)
    db.log("draft", id_caso, (f.borrador or {}).get("generador", ""))
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


@app.get("/api/audit")
def audit():
    return db.audit()


@app.get("/api/export/fichas.jsonl", response_class=PlainTextResponse)
def export_fichas():
    """fichas.jsonl con el estado actual (incluye borrador y revisión) para registrar en Notion."""
    return "\n".join(json.dumps(d, ensure_ascii=False) for d in db.all_fichas())


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
    sembrar()
    db.log("reset")
    return {"ok": True, "fichas": len(db.all_fichas())}
