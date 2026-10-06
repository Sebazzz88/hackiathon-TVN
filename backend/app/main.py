import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import db, scoring, agent_interface as agent
from .models import Ficha, QueryIn, QueryOut, ReviewIn


@asynccontextmanager
async def lifespan(_):
    db.init()
    if not db.all_fichas():
        for f in agent.build_candidates():
            db.save(scoring.aplicar(f))
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
    return {"ok": True, "agent_mode": agent.AGENT_MODE, "reglas": scoring.VERSION}


@app.get("/api/quality-report")
def quality_report():
    p = db.DATA_DIR / "processed" / "quality_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"disponible": False}


@app.get("/api/inbox", response_model=list[Ficha])
def inbox(limit: int = 5):
    fs = sorted((Ficha(**d) for d in db.all_fichas()), key=scoring.clave_orden)
    return fs[: max(1, min(limit, 50))]


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
    db.save(f)
    db.log("draft", id_caso)
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
    db.save(f)
    db.log("review", id_caso, f"{r.estado} por {r.revisor}: {r.comentario}")
    return f


@app.get("/api/audit")
def audit():
    return db.audit()
