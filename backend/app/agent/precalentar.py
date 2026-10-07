"""Genera con la IA generativa configurada (Hermes 3 local vía Ollama por defecto) los borradores y respuestas de la
demo y los guarda en caché (data/cache/llm) para presentar sin internet (T10). Con un proveedor en la nube requiere
LLM_API_KEY en .env.

Uso (desde backend/):  .\\.venv\\Scripts\\python -m app.agent.precalentar [--top 10]
"""
import json
import sys
import time

from . import draft, llm, pipeline, query
from .config import ROOT

CONSULTAS_DEMO = [
    "¿Qué dijo S&P sobre el grado de inversión de Panamá?",
    "¿Afectará El Niño los tránsitos por el Canal de Panamá?",
    "¿Cuántas viviendas afectadas dejaron las lluvias en Chiriquí?",
    "¿Quién es la nueva administradora del Canal de Panamá?",
    "¿Se aprobó el presupuesto del Canal de Panamá en la Asamblea?",
]


def main():
    est = llm.estado()
    if not est["conectado"]:
        print(f"La IA generativa no está disponible ({est['motivo']}). Con Ollama: enciende Ollama y corre "
              f"'ollama pull {est['modelo']}'. Con un proveedor en la nube: pon LLM_API_KEY en .env.")
        sys.exit(1)
    llm.precargar()
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 10
    fichas = pipeline.seleccionar(pipeline.analizar()["fichas"])
    elegidas = [f for f in fichas if not f.sintetico][:top] + [f for f in fichas if f.sintetico]
    consultas = list(CONSULTAS_DEMO)
    try:
        consultas += [c["pregunta"] for c in json.loads((ROOT / "eval" / "consultas_noticias.json").read_text(encoding="utf-8"))]
    except FileNotFoundError:
        pass
    costo, t0 = 0.0, time.time()
    print(f"Modelo {est['modelo']} · {len(elegidas)} borradores · {len(dict.fromkeys(consultas))} consultas")
    for f in elegidas:
        b = draft.generar(f)  # seleccionar() ya devuelve las fichas con su puntaje
        m = b.get("meta_llm", {})
        costo += m.get("costo_usd", 0) if m.get("origen") == "llm" else 0
        print(f"  borrador {f.id_caso:<18} {b.get('generador'):<28} afirmaciones={len(b.get('afirmaciones', []))} "
              f"eliminadas={len(b.get('eliminadas', []))}")
    for q in dict.fromkeys(consultas):
        r = query.responder(q, ia=True)
        m = r.meta_llm or {}
        costo += m.get("costo_usd", 0) if m.get("origen") == "llm" else 0
        print(f"  consulta {r.generador or 'extractivo':<28} {q[:60]}")
    print(f"Listo en {time.time() - t0:.0f} s · costo estimado {costo:.4f} USD · caché en {llm.cache_dir()}")
    print("Para la demo offline: git add data/cache/llm; git commit -m 'data: cache LLM demo'; git push")


if __name__ == "__main__":
    main()
