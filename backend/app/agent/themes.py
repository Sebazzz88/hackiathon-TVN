"""Clasificación temática.

IA: similitud semántica (embeddings multilingües) contra frases prototipo por tema (k-NN a prototipos, max).
Baseline: reglas de palabras clave (ver baseline.py). Ambos se comparan en eval/run_eval.py.
"""
import numpy as np

from .embed import embed

PROTOTIPOS = {
    "economia": [
        "economía de Panamá: crecimiento del PIB, inflación y precios",
        "desempleo, empleo y salarios en Panamá",
        "deuda pública, presupuesto del Estado, déficit fiscal y calificación de riesgo",
        "Panama economy, GDP growth, inflation, debt and credit rating",
        "costo de la canasta básica y precios del combustible",
        "inversión extranjera, comercio, bancos y mercado financiero",
    ],
    "logistica_canal": [
        "Canal de Panamá: tránsito de buques y peajes",
        "puertos, contenedores, carga y transporte marítimo",
        "nivel del lago Gatún, agua para el Canal y restricciones de calado",
        "Panama Canal shipping transits, ports and cargo",
        "logística, zona libre de Colón, aduanas y comercio exterior",
        "Autoridad del Canal de Panamá y proyecto del río Indio",
    ],
    "turismo": [
        "turismo en Panamá: llegada de turistas y visitantes",
        "hoteles, ocupación hotelera y cruceros",
        "aeropuerto de Tocumen, vuelos y aerolíneas, Copa Airlines",
        "Panama tourism, travel, visitors and hotels",
        "promoción turística, destinos y festivales",
    ],
    "servicios_publicos": [
        "suministro de agua potable, IDAAN y cortes de agua",
        "electricidad, apagones y tarifas de luz",
        "Caja de Seguro Social, hospitales, medicamentos y salud pública",
        "educación pública, escuelas, docentes y MEDUCA",
        "transporte público, metro de Panamá, buses y carreteras",
        "recolección de basura y saneamiento",
    ],
    "eventos_naturales": [
        "sismo, terremoto o temblor sacude la región",
        "inundaciones, lluvias intensas y alerta del SINAPROC",
        "deslizamientos de tierra, tormentas y vientos fuertes",
        "earthquake, flood, storm or natural disaster",
        "sequía, fenómeno de El Niño y clima extremo",
        "incendio forestal y emergencia ambiental",
    ],
    "regulacion": [
        "Asamblea Nacional aprueba proyecto de ley",
        "decreto ejecutivo, nueva regulación y reforma legal",
        "Corte Suprema de Justicia fallo de inconstitucionalidad",
        "superintendencia, normas, permisos y licencias",
        "reformas a la ley de la Caja de Seguro Social y al Código",
        "Panama new law, regulation, government decree",
    ],
    "otros": [
        "fútbol, deportes y selección nacional",
        "farándula, espectáculos, música y celebridades",
        "homicidio, robo, aprehensión y sucesos policiales",
        "política internacional de otro país sin relación con Panamá",
        "Panama City Florida local news",
        "horóscopo, recetas, entretenimiento y estilo de vida",
        "noticias internacionales de Europa, Estados Unidos, África o Asia",
        "epidemia o brote de enfermedad en otro país",
        "guerra, conflicto armado y diplomacia entre potencias",
        "realeza británica, televisión, cine y personajes famosos",
        "muere leyenda del boxeo, béisbol o atletismo",
        "proceso judicial contra dirigente sindical o exfuncionario",
        "elecciones, partidos políticos y declaraciones de dirigentes",
    ],
}

_P = None


def _protos():
    global _P
    if _P is None:
        labels, textos = [], []
        for t, fr in PROTOTIPOS.items():
            labels += [t] * len(fr)
            textos += fr
        _P = (np.array(labels), embed(textos))
    return _P


SIM_MIN, MARGEN_MIN = 0.40, 0.05  # calibrados: asignaciones erróneas tenían sim < 0.40 o margen < 0.05


def clasificar_vecs(V: np.ndarray):
    """Devuelve lista de (tema, similitud, margen) por fila. Si la similitud o el margen frente al segundo tema
    son bajos, el titular se declara 'otros' (fuera de los 6 temas) en vez de forzar un tema."""
    labels, P = _protos()
    S = V @ P.T
    temas = list(PROTOTIPOS)
    by = np.stack([S[:, labels == t].max(axis=1) for t in temas], axis=1)
    out = []
    for row in by:
        o = np.argsort(-row)
        t, sim, mar = temas[o[0]], float(row[o[0]]), float(row[o[0]] - row[o[1]])
        out.append((t if (sim >= SIM_MIN and mar >= MARGEN_MIN) else "otros", sim, mar))
    return out


def clasificar(textos):
    return clasificar_vecs(embed(textos))
