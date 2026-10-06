# Plan y decisiones

Importar la tabla de backlog como base de datos de Notion (Estado, Responsable, Fecha). Fechas en hora de Panamá.

## Backlog

| # | Tarea | Responsable | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|
| 1 | Auditar repo y resumir el reto | Sebastián + Claude Code | Hecho | 2026-10-06 | `docs/AUDITORIA.md`, `docs/RETO.md` |
| 2 | Descargar y validar snapshot (TVN, GDELT, BM, USGS) | Sebastián + Claude Code | Hecho | 2026-10-06 | `data/raw/manifest.json`, `quality_report.json` |
| 3 | Embeddings locales y clasificación en 6 temas | Sebastián + Claude Code | Hecho | 2026-10-06 | `backend/app/agent/themes.py` |
| 4 | Agrupación de eventos y procedencia independiente | Sebastián + Claude Code | Hecho | 2026-10-06 | `events.py`, prueba T02 |
| 5 | Contexto Banco Mundial/USGS | Sebastián + Claude Code | Hecho | 2026-10-06 | `context.py`, prueba T04 |
| 6 | Puntaje R,I,U,N,E y estado de evidencia | Sebastián + Claude Code | Hecho | 2026-10-06 | `pipeline.py`, prueba T08 |
| 7 | Consultas con abstención | Sebastián + Claude Code | Hecho | 2026-10-06 | `query.py`, pruebas T04–T07 |
| 8 | Borrador con validador de citas y caché LLM | Sebastián + Claude Code | Hecho | 2026-10-06 | `draft.py`, `llm.py`, pruebas T09–T10 |
| 9 | Interfaz de flujo completo | Sebastián + Claude Code | Hecho | 2026-10-06 | `frontend/src/App.jsx` |
| 10 | Benchmark 60 consultas y evaluación vs baseline | Sebastián + Claude Code | Hecho (etiquetas pendientes de revisión) | 2026-10-06 | `eval/` |
| 11 | Revisar etiquetas del benchmark y de temas | Sebastián | Pendiente | — | `eval/etiquetas_*.csv` |
| 12 | Selección independiente de top 5 por un editor | Persona editorial | Pendiente | — | `eval/seleccion_editor.json` |
| 13 | Revisión humana de ≥ 30 afirmaciones (validez de sustento) | Sebastián | Pendiente | — | `eval/resultados/afirmaciones_para_revision.csv` |
| 14 | Generar borradores con LLM y guardar caché para demo offline | Sebastián | Pendiente (requiere clave) | — | `data/cache/llm/` |
| 15 | Cargar espacio Notion y dar acceso al jurado | Sebastián | Pendiente | — | URL de Notion |
| 16 | Ensayar pitch de 10 min con demo offline | Sebastián | Pendiente | — | `docs/11_PITCH.md` |

## Decisiones justificadas (extracto; completo en `docs/09_DECISIONS.md`)

1. **Embeddings locales ONNX en vez de PyTorch o API** (D05): funciona sin internet y pesa ~10 veces menos.
2. **Réplica = criterio léxico, no semántico** (D06): medimos 0,89–0,95 de similitud entre titulares distintos del mismo hecho; el criterio semántico contaba reporteo propio como réplica.
3. **El LLM solo redacta; el puntaje lo calcula código** (D10): reproducible y resistente a inyección.
4. **Ventana de 30 días en lugar del intervalo 2024–2025** (D03): el PDF pide ambas cosas y GDELT solo cubre ~3 meses.
5. **540 celdas del Banco Mundial, no 1.350** (D04): 6 × 6 × 15 = 540.
