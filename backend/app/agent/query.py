"""Consultas en español con recuperación semántica y abstención (T04, T05, T06, T07).

Orden de decisión:
 1. Consulta con intento de inyección -> se rechaza (abstención) sin revelar nada.
 2. Pregunta por un indicador (inflación, PIB, desempleo...) -> Banco Mundial con país, año y unidad.
    'hoy/actual' o año fuera de 2010–2024 -> abstención explicando que solo hay datos anuales.
 3. Pregunta sobre noticias -> recuperación semántica de eventos; si la similitud máxima < umbral -> abstención.
    Si pide una cifra y ningún titular recuperado la contiene -> abstención (CU-04).
    Si el evento tiene versiones incompatibles -> se muestran todas (T05).
La respuesta es extractiva: solo reproduce titulares/valores con su cita. No se usa LLM aquí.
"""
import re

import numpy as np

from ..models import Cita, QueryOut
from . import pipeline
from .baseline import norm
from .config import LEYENDA, SIM_QUERY_MIN
from .context import NOMBRE_PAIS, NOMBRES, PAISES, fmt_valor, item_indicador, ultimo_valor
from .embed import embed
from .security import es_inyeccion

AHORA = ["hoy", "actual", "actualmente", "ahora", "este mes", "esta semana", "en este momento", "today", "current",
         "proximo ano", "el ano que viene", "sera", "seran", "pronostico", "proyeccion", "prevision", "next year", "forecast"]
PIDE_CIFRA = ["cuanto", "cuantos", "cuantas", "cifra", "monto", "porcentaje", "%", "numero de", "cantidad", "how many", "how much"]
# Orden de lo más específico a lo más general: "porcentaje de la población que usa internet" es internet, no población;
# "exportaciones en el PIB" es exportaciones, no crecimiento. En consultas, "precio" solo NO activa inflación
# (gasolina o diésel son noticias, no el IPC anual).
CLAVES_Q = {
    "IT.NET.USER.ZS": ["internet", "conectividad", "banda ancha"],
    "NE.EXP.GNFS.ZS": ["exportaciones", "exports"],
    "SL.UEM.TOTL.ZS": ["desempleo", "tasa de empleo", "unemployment"],
    "FP.CPI.TOTL.ZG": ["inflacion", "indice de precios", "ipc", "costo de vida", "inflation"],
    "SP.POP.TOTL": ["poblacion", "habitantes", "population"],
    "NY.GDP.MKTP.KD.ZG": ["pib", "crecimiento economico", "crecimiento de la economia", "crecio la economia", "gdp"],
}


OTROS_PAISES = ["chile", "argentina", "peru", "ecuador", "venezuela", "bolivia", "brasil", "uruguay", "paraguay",
                "honduras", "nicaragua", "el salvador", "cuba", "haiti", "jamaica", "estados unidos", "eeuu", "canada",
                "espana", "francia", "alemania", "china", "japon", "india", "islandia", "reino unido", "italia", "rusia"]


def _indicador(q):
    for ind, cl in CLAVES_Q.items():
        if any(c in q for c in cl):
            return ind
    return None


def _pais(q):
    for p, nombres in PAISES.items():
        if p != "PAN" and any(norm(x) in q for x in nombres):
            return p
    return "PAN"


def _abst(faltante, metodo, versiones=None):
    return QueryOut(abstencion=True, faltante=faltante, metodo=metodo, versiones=versiones or [])


def responder(pregunta: str) -> QueryOut:
    q = norm(pregunta)
    if es_inyeccion(pregunta):
        return _abst(["La consulta contiene instrucciones para cambiar las reglas o revelar información interna. "
                      "Se rechaza: el agente solo responde con evidencia del corpus."], "control_inyeccion")
    ind = _indicador(q)
    if ind:
        otro = next((p for p in OTROS_PAISES if f" {p}" in f" {q}"), None)
        if otro:
            return _abst([f"El paquete del Banco Mundial solo cubre Panamá, Costa Rica, Colombia, República Dominicana, "
                          f"México y Guatemala; no hay datos de «{otro}». No se sustituye por otro país."], "indicador_bm")
        pais = _pais(q)
        anios = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", q)]
        if any(f" {a} " in f" {q} " for a in AHORA) or any(y > 2024 or y < 2010 for y in anios):
            y, _ = ultimo_valor(pais, ind)
            return _abst([f"El paquete solo tiene datos ANUALES del Banco Mundial 2010–2024 para {NOMBRES[ind].lower()}; "
                          f"no existe una medición de hoy ni del año pedido. Último año disponible para "
                          f"{NOMBRE_PAIS[pais]}: {y}. Pregunte por ese año para ver el valor citado."], "indicador_bm")
        y = anios[0] if anios else ultimo_valor(pais, ind)[0]
        it = item_indicador(pais, ind, y) if y else None
        if not it or it["valor"] is None:
            return _abst([f"El Banco Mundial no reporta {NOMBRES[ind].lower()} de {NOMBRE_PAIS[pais]} para {y} "
                          "(valor nulo en la fuente). No se rellena ni se estima."], "indicador_bm")
        txt = (f"{it['texto']}. Fuente: Banco Mundial ({it['indicador_id']}). {it['limitacion']}")
        return QueryOut(abstencion=False, respuesta=txt, metodo="indicador_bm", base="indicadores oficiales",
                        citas=[Cita(afirmacion=it["texto"], tipo="hecho", id_evidencia=it["id_evidencia"], campo="valor")],
                        ids_fuente=[it["id_evidencia"]])
    # --- noticias ---
    a = pipeline.analizar()
    fichas = list(a["fichas"])  # los casos sintéticos se incluyen pero se rotulan como tales
    if not fichas:
        return _abst(["No hay noticias cargadas en el snapshot."], "recuperacion_semantica")
    qv = embed([pregunta])[0]
    titulos = [f.titulo for f in fichas]
    T = embed(titulos)
    sims = T @ qv
    orden = np.argsort(-sims)[:3]
    if float(sims[orden[0]]) < SIM_QUERY_MIN:
        return _abst([f"Ningún evento del corpus responde a la consulta (similitud máxima {float(sims[orden[0]]):.2f} "
                      f"< umbral {SIM_QUERY_MIN}). Se necesitaría una fuente que cubra ese tema."], "recuperacion_semantica")
    top = [fichas[i] for i in orden if float(sims[i]) >= SIM_QUERY_MIN]
    if any(c in q for c in PIDE_CIFRA):
        con_cifra = [f for f in top if re.search(r"\d", f.titulo)]
        if not con_cifra:
            return _abst(["Los titulares relacionados no contienen la cifra pedida y no se leyó el artículo completo. "
                          "No se inventa un número: se requiere la fuente primaria."], "recuperacion_semantica")
    citas, partes, versiones, ids = [], [], [], []
    for f in top:
        n0 = next((n for n in f.noticias if n["id"] in f.ids_fuente and not n.get("inyeccion_detectada")), None)
        if not n0:
            continue
        citas.append(Cita(afirmacion=f"{n0['medio']} publicó: «{n0['titulo']}»", tipo="declaracion",
                          id_evidencia=n0["id"], campo="titulo"))
        partes.append(f"• {'[CASO SINTÉTICO DE PRUEBA] ' if f.sintetico else ''}{n0['titulo']} ({n0['medio']}; {f.registros} titular(es), "
                      f"{f.fuentes_independientes} procedencia(s) independiente(s); evidencia {f.estado_evidencia.replace('_', ' ')})")
        ids += f.ids_fuente
        for k in f.contradicciones:
            versiones.append(k)
            for v in k["versiones"]:
                citas.append(Cita(afirmacion=f"Versión: {v['valor']:g} según {v['medio']}", tipo="declaracion",
                                  id_evidencia=v["id"], campo="titulo"))
    if not citas:
        return _abst(["Los registros recuperados no son evidencia utilizable (posible inyección)."], "recuperacion_semantica")
    txt = "Eventos relacionados en el corpus:\n" + "\n".join(partes)
    if versiones:
        txt += "\nHay versiones incompatibles: se muestran todas; verificación pendiente."
    txt += f"\n{LEYENDA}"
    return QueryOut(abstencion=False, respuesta=txt, citas=citas, ids_fuente=ids, versiones=versiones,
                    metodo="recuperacion_semantica", base="titular/metadatos")
