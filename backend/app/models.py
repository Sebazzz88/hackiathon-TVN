from typing import Literal, Optional
from pydantic import BaseModel, Field

Estado = Literal["nuevo", "en_revision", "requiere_evidencia", "aprobado_como_borrador", "descartado"]
EstadoEvidencia = Literal["insuficiente", "parcial", "suficiente_para_borrador"]


class Componentes(BaseModel):  # cada uno normalizado 0-1
    R: float = Field(ge=0, le=1)
    I: float = Field(ge=0, le=1)
    U: float = Field(ge=0, le=1)
    N: float = Field(ge=0, le=1)
    E: float = Field(ge=0, le=1)


class Cita(BaseModel):
    afirmacion: str
    tipo: Literal["hecho", "declaracion", "inferencia", "hipotesis"]
    id_evidencia: str  # id_noticia / indicador / id de evento USGS
    campo: str         # campo, pasaje o página que respalda


class Ficha(BaseModel):  # espejo de fichas.jsonl
    id_caso: str
    modalidad: Literal["tvn_principal", "tvn_digital", "banca"] = "tvn_principal"
    titulo: str
    ids_fuente: list[str]
    afirmaciones: list[str] = []
    citas: list[Cita] = []
    componentes: Componentes
    puntaje: float = 0
    banda: str = ""
    reglas_version: str = ""
    estado_evidencia: EstadoEvidencia
    faltante: list[str] = []
    base: str = "titular/metadatos"
    borrador: Optional[dict] = None
    estado_revision: Estado = "nuevo"
    sintetico: bool = False


class QueryIn(BaseModel):
    pregunta: str = Field(min_length=3, max_length=500)


class QueryOut(BaseModel):
    abstencion: bool
    respuesta: Optional[str] = None
    citas: list[Cita] = []
    ids_fuente: list[str] = []
    faltante: list[str] = []


class ReviewIn(BaseModel):
    estado: Estado
    revisor: str = Field(min_length=2, max_length=80)
    comentario: str = Field(default="", max_length=500)
