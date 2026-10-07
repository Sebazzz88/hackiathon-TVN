"""Carga del snapshot congelado (data/raw + data/processed) y de los casos controlados sintéticos."""
import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from urllib.parse import urlparse

from .config import data_dir


def parse_dt(s: str):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


@dataclass
class Noticia:
    id: str
    titulo: str
    url: str
    medio: str
    idioma: str
    fecha_publicacion: str
    fecha_deteccion: str
    origen: str
    sintetico: bool = False
    caso: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def fecha_ref(self):
        """Fecha para urgencia/orden: publicación si existe; si no, detección (GDELT seendate)."""
        return parse_dt(self.fecha_publicacion) or parse_dt(self.fecha_deteccion)

    @property
    def dominio(self):
        return (self.medio or urlparse(self.url).netloc).lower().removeprefix("www.")

    def as_dict(self):
        return {"id": self.id, "titulo": self.titulo, "url": self.url, "medio": self.dominio, "idioma": self.idioma,
                "fecha_publicacion": self.fecha_publicacion or None, "fecha_deteccion": self.fecha_deteccion or None,
                "origen": self.origen, "sintetico": self.sintetico}


def _read_csv(p):
    if not p.exists():
        return []
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def noticias() -> tuple:
    d = data_dir()
    rows = _read_csv(d / "processed" / "noticias_ok.csv") or _read_csv(d / "raw" / "noticias.csv")
    out = [Noticia(r["id_noticia"], r["titulo"].strip(), r["url"], r["medio"], r.get("idioma", ""),
                   r.get("fecha_publicacion", ""), r.get("fecha_deteccion", ""), r.get("origen", ""))
           for r in rows if r.get("titulo", "").strip()]
    for r in _read_csv(d / "synthetic" / "casos_controlados.csv"):
        out.append(Noticia(r["id_noticia"], r["titulo"].strip(), r["url"], r["medio"], r["idioma"],
                           r["fecha_publicacion"], r["fecha_deteccion"], "sintetico", True, r.get("caso", "")))
    return tuple(out)


@lru_cache(maxsize=1)
def indicadores() -> dict:
    """{(pais, indicador, anio): {valor|None, unidad, fuente_url, ...}} con nulos explícitos."""
    out = {}
    for r in _read_csv(data_dir() / "raw" / "indicadores.csv"):
        v = r["valor"].strip()
        out[(r["pais_iso3"], r["indicador_id"], int(r["anio"]))] = {
            **r, "anio": int(r["anio"]), "valor": float(v) if v else None}
    return out


@lru_cache(maxsize=1)
def eventos() -> tuple:
    p = data_dir() / "raw" / "eventos.geojson"
    if not p.exists():
        return ()
    feats = json.loads(p.read_text(encoding="utf-8")).get("features", [])
    out = []
    for f in feats:
        pr, (lon, lat, depth) = f["properties"], f["geometry"]["coordinates"][:3]
        out.append({"id": f["id"], "magnitude": pr.get("mag"), "time": pr.get("time"), "updated": pr.get("updated"),
                    "longitude": lon, "latitude": lat, "depth": depth, "place": pr.get("place"),
                    "status": pr.get("status"), "url": pr.get("url")})
    return tuple(out)


@lru_cache(maxsize=1)
def manifest() -> dict:
    p = data_dir() / "raw" / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def fecha_corte():
    """Fecha de corte del snapshot (no 'ahora'): la urgencia se mide contra el snapshot congelado."""
    return parse_dt(manifest().get("fecha_corte_UTC", "")) or datetime.now(timezone.utc)


@lru_cache(maxsize=1)
def registro_evidencia() -> dict:
    """Todas las evidencias citables: id -> {tipo, campos disponibles}."""
    reg = {n.id: {"tipo": "noticia", "campos": {"titulo", "medio", "url", "fecha_publicacion", "fecha_deteccion"}, "obj": n}
           for n in noticias()}
    for (p, i, y), r in indicadores().items():
        reg[f"WB:{p}:{i}:{y}"] = {"tipo": "indicador", "campos": {"valor", "unidad", "anio"}, "obj": r}
    for e in eventos():
        reg[f"USGS:{e['id']}"] = {"tipo": "sismo", "campos": {"magnitude", "time", "place", "depth"}, "obj": e}
    return reg


def registro_publico(id_ev: str):
    """Registro FUENTE de una evidencia citable, listo para mostrar: lo que dice el corpus, sin interpretación.
    None si el id no existe en el corpus (una cita a ese id no es válida)."""
    if id_ev.startswith("AGR:"):
        return {"tipo": "agrupacion", "id": id_ev, "titulo": "Dato calculado por el sistema", "url": None,
                "campos": {"id_caso": id_ev[4:], "metodo": "agrupación semántica de titulares + procedencia (agencia replicada = 1)"},
                "nota": "No es una fuente externa: es el recuento que hizo el sistema al agrupar los titulares del evento."}
    reg = registro_evidencia().get(id_ev)
    if not reg:
        return None
    o = reg["obj"]
    if reg["tipo"] == "noticia":
        nota = "Solo titular y metadatos: no se leyó el artículo."
        if not o.fecha_publicacion:
            nota += " GDELT informa la fecha de DETECCIÓN, no la de publicación."
        return {"tipo": "noticia", "id": id_ev, "titulo": o.titulo, "url": o.url, "sintetico": o.sintetico,
                "campos": {"titulo": o.titulo, "medio": o.dominio, "url": o.url, "idioma": o.idioma or "—",
                           "fecha_publicacion": o.fecha_publicacion or None, "fecha_deteccion": o.fecha_deteccion or None,
                           "origen": o.origen}, "nota": nota}
    if reg["tipo"] == "indicador":
        return {"tipo": "indicador", "id": id_ev, "titulo": f"{o['indicador_id']} · {o['pais_iso3']} · {o['anio']}",
                "url": o["fuente_url"],
                "campos": {"pais": o["pais_iso3"], "indicador": o["indicador_id"], "anio": o["anio"], "valor": o["valor"],
                           "unidad": o["unidad"], "licencia": o["licencia"], "fecha_extraccion": o["fecha_extraccion"]},
                "nota": f"Dato ANUAL del Banco Mundial para {o['anio']}: no es una medición de hoy y puede revisarse."}
    t = datetime.fromtimestamp(o["time"] / 1000, tz=timezone.utc).isoformat(timespec="seconds") if o.get("time") else None
    return {"tipo": "sismo", "id": id_ev, "titulo": f"M{o['magnitude']} · {o['place']}", "url": o["url"],
            "campos": {"magnitude": o["magnitude"], "place": o["place"], "time": t, "depth": o["depth"],
                       "latitude": o["latitude"], "longitude": o["longitude"], "status": o["status"]},
            "nota": "USGS 2024, caja regional lat 5–12, lon −86/−76. Sirve solo como hecho sísmico, no como evidencia de daños."}
