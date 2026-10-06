# Changelog

> Fecha, cambio, autor, PR

Rama `feat/agente` (PR abierto a `main`). Autor: Sebastián, con asistencia de Claude Code.

| Fecha | Cambio | Commit |
|---|---|---|
| 2026-10-05 | Esqueleto inicial: FastAPI + SQLite + React/Vite, modo stub, fórmula de puntaje | ec98db1, 39e11aa |
| 2026-10-06 | Etapa 0: auditoría, `docs/RETO.md`, `docs/AUDITORIA.md`, `.gitignore` restaurado desde `main` | 4629ffc |
| 2026-10-06 | Etapa 2–3: agente live (embeddings locales, temas, eventos, procedencia, contradicciones, contexto BM/USGS, consultas con abstención, borrador con validador, LLM con caché), UI de flujo completo, pruebas T01–T10 | cd50d3c |
| 2026-10-06 | Etapa 1: snapshot real versionado (TVN RSS + GDELT + Banco Mundial + USGS) con manifest SHA-256 | ver `git log` |
| 2026-10-06 | Etapa 4: benchmark de 60 consultas, etiquetas de temas y pares, `eval/run_eval.py` | ver `git log` |
| 2026-10-06 | Etapa 5: README probado, docs 01–12, `docs/notion_export/` | ver `git log` |

## Pruebas fallidas y su corrección (para Notion)

| Prueba | Fallo observado | Causa | Corrección |
|---|---|---|---|
| T05 contradicciones | Las versiones "3 viviendas" y "40 viviendas" no aparecían como contradicción | El criterio de réplica (Jaccard ≥ 0,8) las trataba como la misma procedencia | Una réplica exige las mismas cifras (D08) |
| T05 (pares 2 y 5) | Titulares iguales salvo la cifra quedaban en eventos separados | Cambiar la cifra bajaba la similitud semántica bajo 0,80 | Regla léxica de agrupación sin cifras (D08) |
| Calibración del ranking | Notas internacionales de TVN (American Idol, ébola) en el top 5 | Todo TVN contaba como vínculo con Panamá = 1 y faltaban prototipos de "otros" | D07 y D09 |
