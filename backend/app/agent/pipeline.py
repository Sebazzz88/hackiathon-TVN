"""Pipeline completo: corpus -> embeddings -> temas -> eventos -> procedencia -> contexto -> componentes -> fichas.

Componentes (0–1), documentados en docs/04_AGENT.md. El puntaje P=30R+25I+20U+15N+10E lo calcula scoring.py.
  R Relevancia  = 0.6·vínculo con Panamá + 0.4·ajuste al tema (similitud semántica al prototipo del tema).
  I Impacto     = 0.5·alcance (procedencias independientes, log) + 0.35·alcance sectorial del tema + 0.15·contexto oficial.
  U Urgencia    = decaimiento exponencial por antigüedad respecto del corte del snapshot (vida media 48 h);
                  una noticia recirculada usa su fecha ORIGINAL (T03).
  N Novedad     = 1 − similitud máxima con eventos anteriores (reescalada); los duplicados no suman (T02).
  E Evidencia   = 0.5·min(1, independientes/3) + 0.3·contexto oficial pertinente + 0.2·procedencia identificable.
Estado de evidencia (independiente del puntaje): insuficiente / parcial / suficiente_para_borrador.
"""
import json
import math
import time
from collections import Counter
from functools import lru_cache

import numpy as np

from .. import scoring
from ..models import Cita, Componentes, Ficha
from . import corpus, embed, events, themes
from .baseline import norm
from .config import AGENT_VERSION, LEYENDA, TEMAS, VIDA_MEDIA_URGENCIA_H, data_dir
from .context import contexto
from .security import es_inyeccion

ALCANCE_SECTORIAL = {"servicios_publicos": 1.0, "eventos_naturales": 1.0, "economia": 0.9, "logistica_canal": 0.9,
                     "regulacion": 0.8, "turismo": 0.7, "otros": 0.3}  # supuesto editorial: PENDIENTE validar con editor
PANAMA = ["panam", "canal de panama", "chiriqui", "colon", "darien", "veraguas", "cocle", "bocas del toro", "herrera",
          "los santos", "tocumen", "css", "idaan", "mulino", "asamblea nacional", "sinaproc", "meduca", "gatun", "mop",
          "minsa", "mides", "contraloria", "suntracs", "arraijan", "san miguelito", "pase u", "ifarhu", "caja de ahorros",
          "acp", "etesa", "ensa", "naturgy", "copa airlines", "miraflores", "chepo", "la chorrera", "metro de panama"]
SIN_FECHA_H = 24 * 30  # sin ninguna fecha: se trata como antiguo (urgencia ~0)


def clip(x):
    return float(max(0.0, min(1.0, x)))


def fmt_num(x):
    return f"{x:,.0f}".replace(",", ".") if float(x).is_integer() else f"{x:g}".replace(".", ",")


def vinculo_panama(n):
    """1.0 si el titular menciona Panamá o una entidad panameña; 0.6 si solo el medio es panameño (TVN/.pa también
    publica noticias internacionales); 0.2 en otro caso."""
    t = f" {norm(n.titulo)} "
    if any(f" {p}" in t for p in PANAMA):
        return 1.0
    return 0.6 if (n.dominio.endswith(".pa") or "tvn" in n.dominio or n.origen == "tvn_rss") else 0.2


def fecha_txt(d):
    return d.isoformat(timespec="minutes") if d else ""


def _estado(indep, ctx, contra, recirc, inyeccion):
    if inyeccion or (indep < 2 and not ctx):
        return "insuficiente"
    if contra or recirc or (indep < 3 and not (indep >= 2 and ctx)):
        return "parcial"
    return "suficiente_para_borrador"


def _accion(estado, contra):
    if estado == "insuficiente":
        return "Investigar antes de producir: buscar fuente primaria o segunda procedencia independiente."
    if contra:
        return "Contrastar las versiones con fuente primaria antes de cualquier borrador."
    if estado == "parcial":
        return "Verificar los pendientes; se puede preparar un borrador marcado como preliminar."
    return "Generar borrador y enviarlo a revisión editorial (aprobar no publica)."


def _faltante(miem, indep, ctx, contra):
    out = ["Lectura del artículo completo o comunicado: solo se dispone del titular/metadatos."]
    if indep < 2:
        out.append("Una segunda procedencia independiente (otro medio con reporteo propio o fuente primaria).")
    if not ctx:
        out.append("No hay indicador oficial del paquete con relación sustentada; no se fuerza contexto.")
    if any(not n.fecha_publicacion for n in miem):
        out.append("Fecha de publicación original de algunos registros (GDELT solo informa la fecha de detección).")
    for k in contra:
        out.append(f"Resolver versiones incompatibles sobre «{k['magnitud']}»: "
                   + " vs ".join(f"{fmt_num(v['valor'])} ({v['medio']})" for v in k["versiones"]))
    return out


def _alertas(miem, indep, inyeccion, recirc):
    out = []
    if inyeccion:
        out.append("Posible inyección de instrucciones en la fuente: se trata como dato no confiable; "
                   "no se ejecuta ninguna instrucción y no aporta evidencia.")
    if recirc:
        out.append("Publicación antigua: fecha original "
                   + ", ".join(sorted({n.fecha_publicacion[:10] for n in miem if n.id in recirc}))
                   + " (más de 30 días antes de su detección o del corte). Posible noticia recirculada: "
                   "no se presenta como evento nuevo.")
    if indep < len(miem):
        out.append(f"{len(miem)} titulares agrupados, {indep} procedencia(s) independiente(s): "
                   "la repetición no cuenta como corroboración.")
    return out


def _ficha(idx, ns, V, clas, corte, cent_prev):
    """Construye la ficha de un evento (grupo de índices). cent_prev: centroides de eventos anteriores (novedad)."""
    miem = [ns[i] for i in idx]
    c = V[idx].mean(axis=0)
    c /= np.linalg.norm(c) or 1
    votos = {}  # tema del evento = voto ponderado por similitud
    for i in idx:
        votos[clas[i][0]] = votos.get(clas[i][0], 0) + clas[i][1]
    tema = max(votos, key=votos.get)
    sim_tema = float(np.mean([clas[i][1] for i in idx if clas[i][0] == tema]))
    proc = events.procedencias(miem)
    indep = len(set(proc.values()))
    inyeccion = {n.id for n in miem if es_inyeccion(n.titulo)}
    recirc = {n.id for n in miem if events.recirculada(n, corte)}
    contra = events.contradicciones(miem, proc)
    ctx = [] if inyeccion else contexto([n.titulo for n in miem], tema)

    # --- componentes ---
    pan = max(vinculo_panama(n) for n in miem)
    ajuste = clip((sim_tema - 0.25) / 0.45) if tema != "otros" else 0.1
    R = clip(0.6 * pan + 0.4 * ajuste)
    alcance = clip(math.log2(1 + indep) / math.log2(6))
    I = clip(0.5 * alcance + 0.35 * ALCANCE_SECTORIAL[tema] + 0.15 * bool(ctx))
    fechas = [n.fecha_ref for n in miem if n.fecha_ref]
    ref = min(corpus.parse_dt(n.fecha_publicacion) for n in miem if n.id in recirc) if recirc else (max(fechas) if fechas else None)
    edad_h = max(0.0, (corte - ref).total_seconds() / 3600) if ref else SIN_FECHA_H
    U = clip(0.5 ** (edad_h / VIDA_MEDIA_URGENCIA_H))
    max_prev = max((float(c @ p) for p in cent_prev), default=0.0)
    N = clip((1 - max_prev) / 0.6)
    cent_prev.append(c)
    ident = float(np.mean([1.0 if (n.url.startswith("http") and n.dominio) else 0.0 for n in miem]))
    E = 0.0 if inyeccion else clip(0.5 * min(1, indep / 3) + 0.3 * bool(ctx) + 0.2 * ident)
    estado = _estado(indep, ctx, contra, recirc, inyeccion)

    # --- textos de la ficha ---
    sint = all(n.sintetico for n in miem)
    rep = ns[max(idx, key=lambda i: float(V[i] @ c))]  # titular más representativo (medoide)
    medios = Counter(n.dominio for n in miem)
    citas =[Cita(afirmacion=f"{n.dominio} publicó el titular: «{n.titulo}»", tipo="declaracion",
                  id_evidencia=n.id, campo="titulo") for n in miem if n.id not in inyeccion][:8]
    citas += [Cita(afirmacion=x["texto"], tipo="hecho", id_evidencia=x["id_evidencia"],
                   campo="valor" if x["tipo"] == "indicador" else "magnitude") for x in ctx]
    return Ficha(
        id_caso=("SINT-" if sint else "EV-") + rep.id, titulo=rep.titulo, ids_fuente=[n.id for n in miem],
        afirmaciones=[x.afirmacion for x in citas], citas=citas,
        componentes=Componentes(R=round(R, 3), I=round(I, 3), U=round(U, 3), N=round(N, 3), E=round(E, 3)),
        estado_evidencia=estado, faltante=_faltante(miem, indep, ctx, contra), base="titular/metadatos", sintetico=sint,
        tema=tema, reporta=f"{rep.titulo} — {LEYENDA}",
        reportado_por=[f"{m} ({k})" for m, k in medios.most_common()],
        respaldado=[f"{x.afirmacion} [{x.id_evidencia}·{x.campo}]" for x in citas], accion=_accion(estado, contra),
        fuentes_independientes=indep, registros=len(miem), fuentes_totales=len(miem), procedencias_independientes=indep,
        procedencias=events.resumen_procedencias(miem, proc),
        noticias=[{**n.as_dict(), "procedencia": proc[n.id], "tema_titular": clas[i][0],
                   "inyeccion_detectada": n.id in inyeccion, "recirculada": n.id in recirc} for i, n in zip(idx, miem)],
        contexto=ctx, contradicciones=contra, alertas=_alertas(miem, indep, inyeccion, recirc),
        fecha_primera=fecha_txt(min(fechas) if fechas else None), fecha_ultima=fecha_txt(max(fechas) if fechas else None),
        justificacion={
            "R": f"Vínculo con Panamá {pan:.1f} (mención o medio panameño) · ajuste al tema «{TEMAS[tema]}» {ajuste:.2f}",
            "I": f"Alcance por {indep} procedencia(s) {alcance:.2f} · alcance sectorial {ALCANCE_SECTORIAL[tema]} · "
                 f"contexto oficial {'sí' if ctx else 'no'}",
            "U": f"Antigüedad {edad_h:.0f} h respecto del corte del snapshot; vida media {VIDA_MEDIA_URGENCIA_H} h"
                 + (" · usa fecha ORIGINAL por recirculación" if recirc else ""),
            "N": f"Similitud máxima con eventos anteriores {max_prev:.2f}; duplicados no suman",
            "E": f"{indep} procedencia(s) independiente(s) · contexto oficial {'sí' if ctx else 'no'} · "
                 f"procedencia identificable {ident:.0%}" + (" · E=0 por posible inyección" if inyeccion else ""),
        },
    )


@lru_cache(maxsize=1)
def analizar():
    """Ejecuta el pipeline una vez (cacheado). Devuelve dict con noticias, vectores, temas, grupos y fichas."""
    t0 = time.time()
    ns = list(corpus.noticias())
    V = embed.embed([n.titulo for n in ns])
    clas = themes.clasificar_vecs(V)
    corte = corpus.fecha_corte()
    grupos = events.agrupar(ns, V)
    cent_prev = []
    orden = sorted(grupos, key=lambda g: min((ns[i].fecha_ref or corte) for i in g))  # novedad en orden temporal
    fichas = [_ficha(idx, ns, V, clas, corte, cent_prev) for idx in orden]
    embed.guardar_cache()
    return {"noticias": ns, "V": V, "clas": clas, "grupos": grupos, "fichas": fichas,
            "segundos": round(time.time() - t0, 2), "embed_backend": embed.BACKEND}


@lru_cache(maxsize=1)
def indice_eventos():
    """(fichas, matriz de embeddings de su titular representativo) para la búsqueda semántica de consultas."""
    fichas = analizar()["fichas"]
    return fichas, embed.embed([f.titulo for f in fichas])


def seleccionar(fichas):
    """Todas las fichas con puntaje aplicado, ordenadas (reales primero, luego sintéticos). La bandeja muestra el top N;
    se guardan todas para que cualquier evento recuperado en una consulta tenga su ficha."""
    reales =sorted((scoring.aplicar(f.model_copy()) for f in fichas if not f.sintetico), key=scoring.clave_orden)
    return reales + [scoring.aplicar(f.model_copy()) for f in fichas if f.sintetico]


def exportar_jsonl(fichas):
    p = data_dir() / "processed" / "fichas.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    claves = ("id_caso", "modalidad", "ids_fuente", "afirmaciones", "citas", "puntaje", "componentes", "estado_evidencia",
              "borrador", "estado_revision", "tema", "fuentes_independientes", "sintetico", "reglas_version")
    with open(p, "w", encoding="utf-8") as fh:
        for f in fichas:
            d = f.model_dump()
            fh.write(json.dumps({k: d[k] for k in claves}, ensure_ascii=False) + "\n")
    return p


def info():
    a = analizar()
    return {"agente": AGENT_VERSION, "embeddings": a["embed_backend"], "noticias": len(a["noticias"]),
            "eventos": len(a["grupos"]), "segundos_pipeline": a["segundos"], "fecha_corte": fecha_txt(corpus.fecha_corte())}
