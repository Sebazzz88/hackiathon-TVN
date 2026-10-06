"""Organizar: agrupación de titulares sobre el mismo evento, procedencia independiente (T02),
contradicciones numéricas (T05) y noticias recirculadas (T03)."""
import re
from datetime import timedelta

import numpy as np

from .baseline import norm
from .config import DIAS_RECIRCULADA, SIM_CLUSTER, VENTANA_EVENTO_H
from .corpus import parse_dt

# Agencias: una nota replicada por varios medios cuenta como UNA procedencia.
AGENCIAS = {"efe": "EFE", "afp": "AFP", "ap": "AP", "reuters": "Reuters", "europa press": "Europa Press",
            "ansa": "ANSA", "xinhua": "Xinhua", "prensa latina": "Prensa Latina", "dpa": "DPA",
            "bloomberg": "Bloomberg", "sputnik": "Sputnik"}
DOMINIOS_AGENCIA = {"efe.com": "EFE", "swissinfo.ch": "EFE", "apnews.com": "AP", "reuters.com": "Reuters",
                    "afp.com": "AFP", "europapress.es": "Europa Press", "ansa.it": "ANSA", "xinhuanet.com": "Xinhua",
                    "prensa-latina.cu": "Prensa Latina", "dpa.com": "DPA", "bloomberg.com": "Bloomberg"}
_RX_AG = re.compile(r"(?:^|[\s(\[|:-])(" + "|".join(re.escape(a) for a in AGENCIAS) + r")(?:$|[\s)\]|:.,-])")


def agencia(n):
    if n.dominio in DOMINIOS_AGENCIA:
        return DOMINIOS_AGENCIA[n.dominio]
    m = _RX_AG.search(" " + norm(n.titulo) + " ")
    if m and m.group(1) != "ap":  # "ap" en minúsculas es ambiguo; solo cuenta si aparece "(AP)" literal
        return AGENCIAS[m.group(1)]
    if "(AP)" in n.titulo or n.titulo.startswith("AP "):
        return "AP"
    return None


def titulo_base(t):
    """Quita sufijos de medio ('... - La Prensa', '... | TVN') y marcas de agencia para comparar réplicas."""
    t = re.split(r"\s[-|–—]\s(?=[^-|–—]{2,40}$)", t)[0]
    t = re.sub(r"\((efe|afp|ap|reuters|europa press)\)|^(efe|afp|ap|reuters)\s*[:-]\s*", "", t, flags=re.I)
    return norm(t)


def agrupar(noticias, V: np.ndarray):
    """Agrupación 'líder' en orden temporal: un registro se une al grupo cuyo centroide supera SIM_CLUSTER
    y cuya última fecha está dentro de la ventana. Los sintéticos solo se agrupan entre sí."""
    orden = sorted(range(len(noticias)), key=lambda i: (noticias[i].fecha_ref or parse_dt("1970-01-01"), noticias[i].id))
    grupos = []  # dict(idx=[...], suma=vec, ultima=dt, sint=bool)
    for i in orden:
        n, v = noticias[i], V[i]
        best, bs = None, SIM_CLUSTER
        for g in grupos:
            if g["sint"] != n.sintetico:
                continue
            if n.fecha_ref and g["ultima"] and (n.fecha_ref - g["ultima"]) > timedelta(hours=VENTANA_EVENTO_H):
                continue
            c = g["suma"] / np.linalg.norm(g["suma"])
            s = float(c @ v)
            if s < bs and jaccard(sin_cifras(n.titulo), g["lex"]) >= JACCARD_REPLICA:
                s = bs  # mismo titular salvo las cifras: mismo evento (posible contradicción)
            if s >= bs:
                best, bs = g, s
        if best is None:
            grupos.append({"idx": [i], "suma": v.copy(), "ultima": n.fecha_ref, "sint": n.sintetico,
                           "lex": sin_cifras(n.titulo)})
        else:
            best["idx"].append(i)
            best["suma"] += v
            if n.fecha_ref and (not best["ultima"] or n.fecha_ref > best["ultima"]):
                best["ultima"] = n.fecha_ref
    return [g["idx"] for g in grupos]


JACCARD_REPLICA = 0.8  # réplica = mismo texto (léxico). La similitud semántica NO sirve: titulares distintos del
                       # mismo hecho dan 0.89-0.95 con el modelo, así que contaría reporteo propio como réplica.


def jaccard(a, b):
    x, y = set(a.split()), set(b.split())
    return len(x & y) / len(x | y) if x and y else 0.0


def sin_cifras(t):
    return " ".join(w for w in titulo_base(t).split() if not w[0].isdigit())


def procedencias(miembros, V):
    """Asigna procedencia a cada registro del grupo. Dos registros de medios distintos con el mismo titular
    base (o Jaccard léxico >= JACCARD_REPLICA) son réplicas de una misma fuente. Etiquetas:
    agencia:X (si algún miembro de la réplica cita agencia) > replica:<primer medio> > medio:<dominio>.
    Devuelve {id_noticia: etiqueta}. Fuentes independientes = número de etiquetas distintas."""
    k = len(miembros)
    padre = list(range(k))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    bases = [titulo_base(n.titulo) for n, _ in miembros]
    for i in range(k):
        for j in range(i):
            (a, va), (b, vb) = miembros[i], miembros[j]
            if (a.dominio != b.dominio and (bases[i] == bases[j] or jaccard(bases[i], bases[j]) >= JACCARD_REPLICA)
                    and sorted(cifras(a.titulo)) == sorted(cifras(b.titulo))):  # mismas cifras: si difieren, son versiones distintas
                padre[raiz(i)] = raiz(j)
    comp = {}
    for i in range(k):
        comp.setdefault(raiz(i), []).append(i)
    proc = {}
    for idx in comp.values():
        ags = [agencia(miembros[i][0]) for i in idx]
        ag = next((x for x in ags if x), None)
        if ag:
            et = f"agencia:{ag}"
        elif len(idx) > 1:
            et = f"replica:{miembros[idx[0]][0].dominio}"
        for i in idx:
            proc[miembros[i][0].id] = et if (ag or len(idx) > 1) else f"medio:{miembros[i][0].dominio}"
    return proc


_RX_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:(mil|millones|millon)\s+(?:de\s+)?)?(%|por ciento|[a-záéíóúñ]{4,})?", re.I)
_IGNORAR = {"anos", "años", "horas", "dias", "días", "meses", "minutos", "segundos", "edicion", "edición"}
_NO_SUST = {"para", "desde", "hasta", "entre", "sobre", "segun", "según", "este", "esta", "cada", "durante"}


def cifras(titulo):
    """[(magnitud, valor)] p. ej. '20 mil clientes' -> ('client', 20000). Se ignoran años y duraciones."""
    out = []
    for v, escala, u in _RX_NUM.findall(titulo):
        x = float(v.replace(",", "."))
        un = norm(u or "")
        if not escala and 1900 <= x <= 2100:
            continue
        if escala:
            x *= 1000 if norm(escala) == "mil" else 1_000_000
        if not un or un in _NO_SUST:
            un = norm(escala) if escala else ""
        if not un or un in _IGNORAR:
            continue
        out.append((un[:6], x))
    return out


def contradicciones(miembros, proc):
    """Cifras incompatibles para la misma magnitud entre procedencias distintas. No se elige ninguna."""
    vistos = {}
    for n in miembros:
        for clave, x in cifras(n.titulo):
            vistos.setdefault(clave, []).append({"valor": x, "id": n.id, "medio": n.dominio, "procedencia": proc[n.id],
                                                 "titulo": n.titulo})
    out = []
    for clave, vs in vistos.items():
        valores = {v["valor"] for v in vs}
        if len(valores) > 1 and len({v["procedencia"] for v in vs}) > 1:
            out.append({"magnitud": clave, "versiones": vs,
                        "nota": "Versiones incompatibles; el sistema no elige una. Requiere verificación con fuente primaria."})
    return out


def recirculada(n, corte):
    """Publicación original muy anterior a la detección o al corte -> no es un evento nuevo (T03)."""
    pub, det = parse_dt(n.fecha_publicacion), parse_dt(n.fecha_deteccion)
    ref = det or corte
    return bool(pub and ref and (ref - pub).days > DIAS_RECIRCULADA)
