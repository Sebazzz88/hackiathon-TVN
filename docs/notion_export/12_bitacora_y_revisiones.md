# Bitácora de decisiones y revisiones humanas (generado)

Generado por `backend/app/notion_export.py` desde la tabla `audit` y las fichas de la base del sistema (`data/app.db`), más la tabla de decisiones de `docs/09_DECISIONS.md`. Horas en Panamá.

## Revisiones humanas registradas

| Fecha | Caso | Decisión | Persona | Comentario |
|---|---|---|---|---|
| 2026-10-07 10:52 (Panamá) | `EV-T7bb199ba28` | requiere evidencia | sebas | esto no es real    |

## Actividad del sistema (tabla audit)

| Acción | Veces |
|---|---|
| draft | 17 |
| query | 8 |
| review | 1 |

Últimos 20 eventos:

| Fecha | Acción | Caso | Detalle |
|---|---|---|---|
| 2026-10-07 11:21 (Panamá) | query | — | abstencion=True |
| 2026-10-07 11:20 (Panamá) | query | — | abstencion=True |
| 2026-10-07 11:20 (Panamá) | query | — | abstencion=True |
| 2026-10-07 10:54 (Panamá) | query | — | abstencion=False |
| 2026-10-07 10:52 (Panamá) | review | EV-T7bb199ba28 | requiere_evidencia por sebas: esto no es real    |
| 2026-10-07 10:52 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |
| 2026-10-07 10:51 (Panamá) | draft | EV-T7bb199ba28 | cache:hermes3:3b |

## Decisiones de diseño

Fuente: `docs/09_DECISIONS.md` (alternativas y justificación completas allí).

| # | Fecha | Decisión |
|---|---|---|
| D01 | 2026-10-06 | Modalidad TVN editorial únicamente |
| D02 | 2026-10-06 | RSS de TVN = `https://www.tvn-2.com/rss/` (referencia [2] del PDF) y solo título, URL y fecha |
| D03 | 2026-10-06 | Ventana de noticias = últimos 30 días; no se aplica el intervalo [2024-01-01, 2025-10-01) |
| D04 | 2026-10-06 | Banco Mundial: cuadrícula completa de 540 celdas (6 × 6 × 15) |
| D05 | 2026-10-06 | Embeddings locales con fastembed/ONNX (`paraphrase-multilingual-MiniLM-L12-v2`, 0,22 GB) |
| D06 | 2026-10-06 | Réplica de agencia = agencia citada o texto casi idéntico (Jaccard ≥ 0,8) con las mismas cifras |
| D07 | 2026-10-06 | Clasificación con umbral: similitud ≥ 0,40 y margen ≥ 0,05; si no, "otros" |
| D08 | 2026-10-06 | Titulares iguales salvo cifras = mismo evento |
| D09 | 2026-10-06 | Vínculo con Panamá: 1,0 si el titular menciona Panamá o una entidad panameña; 0,6 si solo el medio es panameño |
| D10 | 2026-10-06 | El LLM solo redacta; puntaje, estado de evidencia y contexto los calcula código |
| D11 | 2026-10-06 | Validador de citas en código, incluido control de cifras |
| D12 | 2026-10-06 | Borrador con caché de LLM + plantilla determinista |
| D13 | 2026-10-06 | Urgencia medida contra la fecha de corte del snapshot, no contra "ahora" |
| D14 | 2026-10-06 | Casos sintéticos (inyección, contradicciones, recirculada, agencia) en archivo aparte y rotulados |
| D15 | 2026-10-06 | Normalizar espaciado de titulares GDELT en `processed/`; `raw/` intacto |
| D16 | 2026-10-06 | IA generativa local: Hermes 3 3B vía Ollama por defecto |
| D17 | 2026-10-06 | Borrador híbrido con modelos locales: hechos por código y redacción editorial por la IA |
| D18 | 2026-10-06 | En Consultar, la IA se pide con un botón; la respuesta inmediata es extractiva |
