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
    # --- Campos explicativos (opcionales; los llena el agente en modo live) ---
    tema: str = ""
    reporta: str = ""                      # qué se reporta
    reportado_por: list[str] = []          # quién lo reporta
    respaldado: list[str] = []             # qué está respaldado (con id de evidencia)
    accion: str = ""                       # acción recomendada al usuario
    fuentes_independientes: int = 0        # procedencias distintas (agencia replicada = 1)
    fuentes_totales: int = 0               # notas/titulares agrupados en el evento (duplicados incluidos)
    procedencias_independientes: int = 0   # procedencias distintas: mismo dominio o misma agencia = 1
    procedencias: list[dict] = []          # desglose: quién, de qué tipo y cuántas notas
    registros: int = 0                     # titulares agrupados (duplicados incluidos)
    noticias: list[dict] = []              # registros agrupados con medio, fechas y procedencia
    contexto: list[dict] = []              # indicadores BM / eventos USGS con período y unidad
    contradicciones: list[dict] = []       # versiones incompatibles visibles (T05)
    alertas: list[str] = []                # recirculada, posible inyección, etc.
    justificacion: dict = {}               # explicación de cada componente R,I,U,N,E
    fecha_primera: str = ""
    fecha_ultima: str = ""
    revisiones: list[dict] = []            # historial de revisión humana


class BandejaItem(BaseModel):
    """Lo mínimo que necesita la lista de la agenda (la ficha completa se pide al abrirla)."""
    id_caso: str
    titulo: str
    tema: str = ""
    puntaje: float
    banda: str
    componentes: Componentes
    estado_evidencia: EstadoEvidencia
    estado_revision: Estado
    fuentes_independientes: int = 0
    fuentes_totales: int = 0
    procedencias_independientes: int = 0
    registros: int = 0
    fecha_ultima: str = ""
    sintetico: bool = False


class Bandeja(BaseModel):
    total: int        # fichas que cumplen el filtro (no solo las devueltas)
    limit: int
    items: list[BandejaItem]


class QueryIn(BaseModel):
    pregunta: str = Field(min_length=3, max_length=500)
    ia: bool = False  # True = pedir respuesta redactada por la IA generativa (puede tardar con un modelo local)


EstadoConsulta = Literal["respondida", "abstencion", "contradiccion"]


class QueryOut(BaseModel):
    estado: EstadoConsulta = "respondida"   # respondida | abstencion | contradiccion
    accion: str = ""                         # qué debe hacer la persona ahora
    abstencion: bool
    respuesta: Optional[str] = None
    citas: list[Cita] = []
    ids_fuente: list[str] = []
    faltante: list[str] = []
    versiones: list[dict] = []   # contradicciones relevantes a la consulta
    eventos: list[dict] = []     # eventos recuperados (para abrir su ficha)
    afirmaciones: list[dict] = []  # respuesta redactada por IA, ya validada (texto, tipo, citas)
    eliminadas: list[dict] = []    # afirmaciones de la IA descartadas por el validador
    generador: str = ""            # extractivo | llm:<modelo> | cache:<modelo>
    meta_llm: dict = {}            # tokens, costo y segundos de la llamada (sin datos sensibles)
    validador: dict = {}           # emitidas / válidas / eliminadas por el validador y por qué
    ia_disponible: bool = False    # la UI puede ofrecer "Redactar con IA"
    base: str = "titular/metadatos"
    metodo: str = ""


class ReviewIn(BaseModel):
    estado: Estado
    revisor: str = Field(min_length=2, max_length=80)
    comentario: str = Field(default="", max_length=500)
