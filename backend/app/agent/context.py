"""Contextualizar: relacionar un evento con indicadores del Banco Mundial (T04) o sismos USGS.
Regla: solo se adjunta contexto si hay relación sustentada (palabra clave del indicador en los titulares,
o tema 'economia' para crecimiento/inflación). Si no hay relación, no se fuerza: se declara la ausencia."""
from .baseline import norm
from .corpus import eventos, indicadores

NOMBRES = {
    "NY.GDP.MKTP.KD.ZG": "Crecimiento del PIB",
    "FP.CPI.TOTL.ZG": "Inflación (precios al consumidor)",
    "SL.UEM.TOTL.ZS": "Desempleo",
    "SP.POP.TOTL": "Población total",
    "IT.NET.USER.ZS": "Personas que usan internet",
    "NE.EXP.GNFS.ZS": "Exportaciones de bienes y servicios",
}
CLAVES = {
    "NY.GDP.MKTP.KD.ZG": ["pib", "crecimiento econom", "economia", "gdp", "econom"],
    "FP.CPI.TOTL.ZG": ["inflacion", "precio", "canasta", "costo de vida", "inflation"],
    "SL.UEM.TOTL.ZS": ["desempleo", "empleo", "trabajo", "unemployment", "jobs"],
    "SP.POP.TOTL": ["poblacion", "censo", "habitantes", "population"],
    "IT.NET.USER.ZS": ["internet", "conectividad", "banda ancha", "digital"],
    "NE.EXP.GNFS.ZS": ["exportacion", "export", "comercio exterior"],
}
PAISES = {"PAN": ["panama", "panamá"], "CRI": ["costa rica"], "COL": ["colombia"], "DOM": ["republica dominicana", "dominicana"],
          "MEX": ["mexico", "méxico"], "GTM": ["guatemala"]}
NOMBRE_PAIS = {"PAN": "Panamá", "CRI": "Costa Rica", "COL": "Colombia", "DOM": "República Dominicana", "MEX": "México", "GTM": "Guatemala"}
SISMO = ["sismo", "terremoto", "temblor", "earthquake", "magnitud", "quake", "sismic"]


def fmt_valor(v, unidad):
    if v is None:
        return "sin dato (nulo en la fuente)"
    if unidad == "personas":
        return f"{v:,.0f} personas".replace(",", ".")
    return f"{v:.2f}".replace(".", ",") + f" ({unidad})"


def ultimo_valor(pais, ind):
    """Último año con valor no nulo. Devuelve (anio, fila) o (None, None)."""
    tab = indicadores()
    for y in range(2024, 2009, -1):
        r = tab.get((pais, ind, y))
        if r and r["valor"] is not None:
            return y, r
    return None, None


def item_indicador(pais, ind, anio):
    r = indicadores().get((pais, ind, anio))
    if not r:
        return None
    return {
        "tipo": "indicador", "id_evidencia": f"WB:{pais}:{ind}:{anio}", "pais": pais, "indicador_id": ind,
        "nombre": NOMBRES[ind], "anio": anio, "valor": r["valor"], "unidad": r["unidad"],
        "texto": f"{NOMBRES[ind]}, {NOMBRE_PAIS[pais]}, {anio}: {fmt_valor(r['valor'], r['unidad'])}",
        "fuente_url": r["fuente_url"], "licencia": r["licencia"],
        "limitacion": f"Dato ANUAL del Banco Mundial para {anio}; no es una medición actual. Puede revisarse.",
    }


def indicadores_relacionados(titulos, tema):
    t = " ".join(norm(x) for x in titulos)
    out = []
    for ind, cl in CLAVES.items():
        hit = any(c in t for c in cl)
        if tema == "economia" and ind in ("NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG"):
            hit = True  # contexto macro básico para cualquier tema económico
        if hit:
            y, _ = ultimo_valor("PAN", ind)
            if y:
                out.append(item_indicador("PAN", ind, y))
    return out


def sismos_relacionados(titulos, tema):
    t = " ".join(norm(x) for x in titulos)
    if tema != "eventos_naturales" or not any(s in t for s in SISMO):
        return []
    evs = [e for e in eventos() if e["magnitude"] is not None]
    if not evs:
        return []
    mx = max(evs, key=lambda e: e["magnitude"])
    return [{
        "tipo": "sismo", "id_evidencia": f"USGS:{mx['id']}", "texto":
        f"Contexto histórico USGS 2024: {len(evs)} sismos M≥3 en la caja lat 5–12, lon −86 a −76; el mayor fue "
        f"M{mx['magnitude']} ({mx['place']}).",
        "conteo_2024": len(evs), "magnitude": mx["magnitude"], "place": mx["place"], "url": mx["url"],
        "limitacion": "La caja regional no equivale al territorio de Panamá. Datos de 2024: no confirman el evento "
                      "reportado ahora ni sirven como evidencia de daños, inundaciones o pérdidas.",
    }]


def contexto(titulos, tema):
    return indicadores_relacionados(titulos, tema) + sismos_relacionados(titulos, tema)
