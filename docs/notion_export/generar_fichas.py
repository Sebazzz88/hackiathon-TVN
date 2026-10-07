#!/usr/bin/env python3
"""Genera docs/notion_export/05_casos_y_evidencias.md desde el pipeline real (sin red, sin LLM).

Uso (desde la raíz del repo):  backend\\.venv\\Scripts\\python docs\\notion_export\\generar_fichas.py
Las fichas salen del snapshot congelado; el borrador es el de la plantilla determinista (o el de la caché del LLM
si existe). La persona revisora y su decisión NO se inventan: quedan para completar en Notion.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend"))
os.environ.setdefault("LLM_OFFLINE", "1")

from app import scoring  # noqa: E402
from app.agent import draft, pipeline  # noqa: E402
from app.agent.config import TEMAS  # noqa: E402

CASOS = [
    ("EV-G226d8217c0", "CU-02: tema económico con serie oficial del Banco Mundial (dato anual, no de hoy)"),
    ("EV-Gb01bc434a8", "Tema económico con 3 procedencias independientes"),
    ("EV-T7bb199ba28", "Caso SIN evidencia suficiente: prioridad alta, una sola fuente"),
    ("EV-G97e3e7b0a7", "CU-03: titulares en varios idiomas agrupados; réplicas cuentan como una fuente"),
    ("EV-G1454ad17a8", "Evento natural con contexto USGS (solo hechos sísmicos)"),
    ("SINT-S-CON-001", "CU-04 / T05 (sintético): versiones incompatibles visibles, sin elegir"),
    ("SINT-S-INY-001", "T07 (sintético): fuente que intenta cambiar las instrucciones"),
]
NOMBRES = {"R": "Relevancia", "I": "Impacto", "U": "Urgencia", "N": "Novedad", "E": "Evidencia"}


def md_ficha(f, motivo, n):
    f = scoring.aplicar(f)
    b = draft.generar(f)
    L = [f"## Ficha {n} · {f.titulo}", "",
         f"**Por qué este caso:** {motivo}", "",
         "| Campo | Valor |", "|---|---|",
         f"| ID del caso | `{f.id_caso}` |",
         f"| Modalidad | TVN editorial |",
         f"| Tema | {TEMAS.get(f.tema, f.tema)} |",
         f"| Sintético | {'Sí (caso controlado de prueba)' if f.sintetico else 'No'} |",
         f"| Puntaje | **{f.puntaje}/100** ({f.banda}) · reglas `{f.reglas_version}` |",
         f"| Estado de evidencia | **{f.estado_evidencia.replace('_', ' ')}** |",
         f"| Titulares / procedencias independientes | {f.registros} / {f.fuentes_independientes} |",
         f"| Base | {f.base} |",
         f"| Estado de revisión | PENDIENTE (lo registra la persona revisora en Notion) |",
         f"| Persona revisora | PENDIENTE |", "",
         "**Puntaje desglosado** (P = 30R + 25I + 20U + 15N + 10E)", "",
         "| Componente | Valor 0–1 | Aporte | Justificación |", "|---|---|---|---|"]
    for k, w in scoring.PESOS.items():
        v = getattr(f.componentes, k)
        L.append(f"| {k} · {NOMBRES[k]} | {v:.2f} | {v * w:.1f} | {f.justificacion.get(k, '')} |")
    L += ["", "**Fuentes (IDs del snapshot)**", "", "| ID | Medio | Procedencia | Publicación (UTC) | Detección (UTC) | Titular |",
          "|---|---|---|---|---|---|"]
    for x in f.noticias:
        L.append(f"| `{x['id']}` | {x['medio']} | {x['procedencia']} | {x.get('fecha_publicacion') or '—'} | "
                 f"{x.get('fecha_deteccion') or '—'} | [{x['titulo'].replace('|', '/')}]({x['url']}) |")
    if f.contexto:
        L += ["", "**Contexto oficial**", ""] + [f"- {c['texto']} (`{c['id_evidencia']}`). {c['limitacion']}" for c in f.contexto]
    if f.contradicciones:
        L += ["", "**Versiones incompatibles**", ""]
        for k in f.contradicciones:
            L += [f"- {v['medio']}: «{v['titulo']}» (`{v['id']}`)" for v in k["versiones"]]
    if f.alertas:
        L += ["", "**Alertas**", ""] + [f"- {a}" for a in f.alertas]
    L += ["", "**Qué falta comprobar**", ""] + [f"- {x}" for x in f.faltante]
    L += ["", f"**Acción recomendada:** {f.accion}", ""]
    L += [f"**Borrador** (generador `{b.get('generador')}`; {b.get('aviso', '')})", ""]
    if b.get("afirmaciones"):
        L += [f"- Título: {b['titulo']}"]
        L += [f"- [{a['tipo']}] ({a['seccion']}) {a['texto']} — " + ", ".join(f"`{c['id_evidencia']}·{c['campo']}`" for c in a["citas"])
              for a in b["afirmaciones"]]
        L += [f"- Preguntas: " + " / ".join(b["preguntas"]),
              f"- Brief {b['brief_palabras']}/250 palabras · guion ~{b['guion_segundos_estimados']} s · copy {b['copy_palabras']}/80 palabras",
              f"- Afirmaciones eliminadas por el validador: {len(b.get('eliminadas', []))}"
              + ("".join(f"\n  - «{e['texto']}» — {e['motivo']}" for e in b.get("eliminadas", [])))]
    L += ["", "---", ""]
    return "\n".join(L)


def main():
    fichas = {f.id_caso: f for f in pipeline.analizar()["fichas"]}
    out = ["# Casos y evidencias (fichas trazables)", "",
           "Generado con `docs/notion_export/generar_fichas.py` desde el snapshot congelado (corte 2026-10-06 21:24 UTC). "
           "Cinco fichas reales, una de ellas con evidencia insuficiente, y dos casos sintéticos de prueba. "
           "Importar cada ficha como página de la base «Casos y evidencias» en Notion; la persona revisora completa "
           "estado y decisión.", ""]
    for n, (cid, motivo) in enumerate(CASOS, 1):
        if cid not in fichas:
            out.append(f"## Ficha {n} · `{cid}` no encontrada en el snapshot actual\n")
            continue
        out.append(md_ficha(fichas[cid], motivo, n))
    p = Path(__file__).with_name("05_casos_y_evidencias.md")
    p.write_text("\n".join(out), encoding="utf-8")
    print("escrito", p)


if __name__ == "__main__":
    main()
