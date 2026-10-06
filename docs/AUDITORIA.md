# Auditoría — Etapa 0 (2026-10-06)

Estado inicial del repo en `feat/agente` (commit 63371a3), antes de cualquier cambio de código.

| Requisito | Estado | Problema | Solución |
|---|---|---|---|
| Ingesta noticias (TVN ≥20 + GDELT, ≥100) | PENDIENTE | `data/raw` vacío; sin `TVN_RSS_URL` no hay registros TVN | Etapa 1: descargar snapshot; configurar RSS de TVN |
| Ingesta Banco Mundial 1.350 celdas | PENDIENTE | Script existe, no ejecutado | Etapa 1 |
| USGS 2024 caja regional | PENDIENTE | Script existe, no ejecutado | Etapa 1 |
| manifest.json + SHA-256 | PARCIAL | Script lo genera; `.gitignore` excluye `data/raw/*` | Etapa 1: versionar snapshot (solo metadatos) |
| Reporte de calidad (T01) | PARCIAL | `validate.py` no valida campos obligatorios ni indicadores/USGS | Etapa 1/4: ampliar validación y test T01 |
| Clasificación 6 temas (NLP) | AUSENTE | `tema` vacío en el CSV | Etapa 2: embeddings locales + prototipos |
| Agrupación de eventos | AUSENTE | — | Etapa 2: similitud de embeddings |
| Independencia de fuentes (T02) | AUSENTE | — | Etapa 2: procedencia por medio/agencia |
| Contexto BM/USGS (T04) | AUSENTE | — | Etapa 2 |
| Componentes R,I,U,N,E | PARCIAL | Fórmula, bandas y desempate OK en `scoring.py`; componentes son DEMO | Etapa 2: cálculo documentado |
| Estado de evidencia independiente | PARCIAL | Modelo OK; valores DEMO | Etapa 2 |
| Contradicciones (T05) | AUSENTE | — | Etapa 2 |
| Consulta con abstención (T06) | PARCIAL | Stub siempre se abstiene | Etapa 2: recuperación + umbral |
| Borrador con citas y tipos (T09) | AUSENTE | Stub vacío | Etapa 2: LLM + validador + fallback offline |
| Anti-inyección (T07) | AUSENTE | — | Etapa 2: delimitación DATO + registro sintético |
| Offline (T10) | PARCIAL | Stub funciona offline; no hay caché LLM | Etapa 2: caché y fallback determinista |
| Baseline | AUSENTE | — | Etapa 2/4 |
| Revisión humana 5 estados | IMPLEMENTADO | Comentario no se captura en la UI | Etapa 3 |
| Aprobación bloqueada con evidencia insuficiente (T08) | IMPLEMENTADO | Test existente pasa | — |
| UI flujo completo | PARCIAL | Falta reporte de calidad, ficha de 5 partes, borrador legible, panel de evaluación, hora de Panamá | Etapa 3 |
| Pruebas T01–T10 | PARCIAL | 3 tests (fórmula, T08, abstención stub) | Etapa 4 |
| benchmark.jsonl 60 + eval | AUSENTE | `eval/` vacío | Etapa 4 (etiquetas requieren revisión humana) |
| README reproducible | PARCIAL | Comandos bash, no PowerShell; sin datos ni modo live | Etapa 5 |
| Docs 01–12 | AUSENTE | Plantillas con "_Pendiente._" | Etapa 5 |
| Export Notion | AUSENTE | — | Etapa 5 (la carga en Notion es manual del usuario) |
| Dependencias fijadas | PARCIAL | `requirements.txt` fijado; frontend sin `package-lock.json` | Etapa 5: versionar lock |
| Higiene git | CORREGIDO | `.gitignore` sobrescrito (faltaban `.venv/`, `venv/`, `data/raw/*`, `.env.*`) | Restaurado desde `origin/main` + `*.db`, `.pytest_cache/` |

**VERIFICADO en Etapa 0:** `pytest -q` → 3 passed. Backend arranca (`/health` responde `agent_mode=stub`). Frontend `npm run build` OK. No hay `.env`, `.db` ni `node_modules` versionados ni en el historial.

**Observaciones:**
- Hay dos entornos: `backend/.venv` (Python 3.13, con dependencias) y `backend/venv` (Python 3.14, vacío). Se usa `.venv`.
- Conflicto en el PDF: pide noticias de los "30 días previos a la extracción" y a la vez "excluir registros fuera de [2024-01-01, 2025-10-01)". GDELT DOC solo cubre ~3 meses móviles, así que con extracción en octubre 2026 ambas reglas son incompatibles. Decisión: priorizar la ventana reciente y documentarlo (docs/09_DECISIONS.md).
