"""Baselines simples (sección 8 del reto): reglas temáticas por palabras clave, búsqueda por palabras clave
y ranking por fecha. Sirven de comparación para medir qué aporta la IA."""
import re
import unicodedata

REGLAS = {
    "economia": ["econom", "pib", "inflacion", "precio", "desempleo", "empleo", "deuda", "presupuesto", "fiscal",
                 "banco", "inversion", "salario", "gdp", "inflation", "debt"],
    "logistica_canal": ["canal", "puerto", "contenedor", "buque", "naviera", "carga", "logistic", "shipping",
                        "gatun", "aduana", "zona libre"],
    "turismo": ["turis", "hotel", "crucero", "tocumen", "aerolinea", "vuelo", "copa airlines", "tourism", "visitante"],
    "servicios_publicos": ["agua", "idaan", "electric", "apagon", "luz", "css", "caja de seguro", "hospital", "salud",
                           "escuela", "educacion", "meduca", "metro", "transporte", "basura"],
    "eventos_naturales": ["sismo", "terremoto", "temblor", "inundacion", "lluvia", "tormenta", "deslizamiento",
                          "sinaproc", "sequia", "incendio", "earthquake", "flood", "storm"],
    "regulacion": ["ley", "decreto", "asamblea", "reforma", "corte suprema", "regulacion", "norma", "superintendencia",
                   "resolucion", "law", "regulation"],
}


def norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9% ]", " ", "".join(c for c in t if not unicodedata.combining(c)))).strip()


def clasificar(titulo):
    """Primer tema con más coincidencias; 'otros' si ninguna regla aplica."""
    t = f" {norm(titulo)} "
    sc = {k: sum(1 for w in ws if (f" {w}" in t)) for k, ws in REGLAS.items()}
    best = max(sc, key=sc.get)
    return best if sc[best] > 0 else "otros"


STOP = set("el la los las de del y o a en un una por para con que se su al es como cual cuales cuanto cuantos "
           "fue son hay sobre the of and in to what is que quien donde cuando panama".split())


def tokens(t):
    return [w for w in norm(t).split() if w not in STOP and len(w) > 2]


def buscar(pregunta, noticias, k=5):
    """Búsqueda por palabras clave (solapamiento de tokens). Devuelve [(score, noticia)]."""
    q = set(tokens(pregunta))
    if not q:
        return []
    res = []
    for n in noticias:
        s = len(q & set(tokens(n.titulo))) / len(q)
        if s > 0:
            res.append((s, n))
    return sorted(res, key=lambda x: -x[0])[:k]


def ranking_por_fecha(grupos):
    """Ranking baseline: el evento más reciente primero."""
    return sorted(grupos, key=lambda g: g["fecha_ultima"] or "", reverse=True)
