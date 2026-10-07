# Arquitectura

> Diagrama y componentes

```
Fuentes públicas (TVN RSS, GDELT DOC 2.0, Banco Mundial API v2, USGS FDSN)
   │  data/scripts/download_snapshot.py  (una vez, con internet)
   ▼
data/raw/  noticias.csv · indicadores.csv · eventos.geojson · manifest.json (SHA-256)
   │  data/scripts/validate.py  → reporte de calidad, separa errores, conserva nulos
   ▼
data/processed/  noticias_ok.csv · noticias_errores.csv · quality_report.json · embeddings.npz · fichas.jsonl
   │  + data/synthetic/casos_controlados.csv (marcados como sintéticos)
   ▼
backend/app/agent/  (AGENT_MODE=live)
   embed.py      embeddings multilingües locales (ONNX) + caché; respaldo léxico sin modelo
   themes.py     clasificación en 6 temas por similitud a prototipos (+ "otros")
   events.py     agrupación de eventos, procedencia (agencia replicada = 1), contradicciones, recirculación
   context.py    Banco Mundial (país, año, unidad) y USGS (solo sismos)
   pipeline.py   componentes R,I,U,N,E + estado de evidencia + ficha explicable
   query.py      consultas: indicadores, recuperación semántica, abstención
   draft.py      borrador (LLM con caché | plantilla) + VALIDADOR de citas
   llm.py        Claude vía SDK oficial, salida JSON por esquema, caché en data/cache/llm
   security.py   detección de inyección y aislamiento de datos
   baseline.py   palabras clave, reglas temáticas, ranking por fecha
   │
backend/app/  FastAPI: scoring.py (P=30R+25I+20U+15N+10E), db.py (SQLite), main.py (API)
   ▼
frontend/ React + Vite (App.jsx, lib.js, views/): Agenda (ficha · fuentes · puntaje · borrador · revisión),
          Consultar, Datos, Evaluación. Rutas por hash para enlaces directos. Sin fuentes ni recursos externos (offline)
   ▼
Revisión humana (5 estados, revisor, comentario) → /api/export/fichas.jsonl → registro manual en Notion
```

## Modelo de datos

- **Ficha** (`backend/app/models.py`, espejo de `fichas.jsonl`): id_caso, ids_fuente, afirmaciones, citas, componentes, puntaje, banda, reglas_version, estado_evidencia, faltante, borrador, estado_revision, más campos explicativos: tema, reporta, reportado_por, respaldado, accion, fuentes_independientes, noticias, contexto, contradicciones, alertas, justificacion, revisiones.
- **Cita:** afirmacion, tipo (hecho / declaracion / inferencia / hipotesis), id_evidencia, campo.
- **IDs de evidencia:** `T…`/`G…` (noticia, hash de URL), `WB:PAIS:INDICADOR:AÑO`, `USGS:<id>`, `AGR:<id_caso>` (dato calculado de agrupación).
- **SQLite:** tablas `fichas`, `audit` (consultas, borradores y revisiones; no guarda el texto de las consultas) y `meta`.

## API

| Método | Ruta | Uso |
|---|---|---|
| GET | /health | modo, versión de reglas y pesos |
| GET | /api/meta | fecha de corte, archivos y SHA-256 del snapshot |
| GET | /api/quality-report | reporte de calidad |
| GET | /api/inbox?limit=5&sinteticos=false&tema=&dias= | bandeja priorizada (limit 1–1000; filtros por tema y ventana de días) |
| GET | /api/fichas/{id} | ficha |
| POST | /api/fichas/{id}/draft | genera borrador |
| POST | /api/fichas/{id}/review | revisión humana |
| POST | /api/query | consulta en español: estado respondida, abstencion o contradiccion, acción sugerida y acción de interfaz validada |
| GET | /api/validador | totales del validador de citas (emitidas, válidas, eliminadas y por qué) |
| GET | /api/evidencia/{id} | registro fuente de una cita (noticia, indicador BM, sismo USGS) |
| GET / POST | /api/jurado/pruebas | última corrida / correr T01–T10 en vivo (subproceso sin ventana, base temporal, sin red) |
| GET | /api/jurado/metricas | agente vs baseline leído de `eval/results.json` |
| GET | /api/eval | info del agente y resultados de evaluación |
| GET | /api/export/fichas.jsonl | exportación para Notion |
| GET | /api/audit | registro de acciones |
| POST | /api/reset | regenera fichas desde el snapshot |
| GET | / | interfaz compilada (`frontend/dist`), si existe: demo en un solo proceso con `run_demo.ps1` o Docker |

Red de seguridad: si la consulta o el borrador fallan por cualquier motivo, la API responde 200 con una abstención que
dice qué hacer (el detalle va al log). Probado en `backend/tests/test_robustez.py`.

## Proporcionalidad

Una sola máquina, sin servicios externos obligatorios. El único componente opcional en red es el LLM, con caché y plantilla de respaldo. Dependencias nuevas: `fastembed` (ONNX, ~0,22 GB de modelo) en vez de PyTorch, y el SDK `anthropic`.
