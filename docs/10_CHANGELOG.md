# Changelog

> Fecha, cambio, autor, PR

Desarrollado en `feat/agente` y fusionado en `main` el 2026-10-07; desde entonces se trabaja en `main`. Autor: Sebastián, con asistencia de Claude Code.

| Fecha | Cambio | Commit |
|---|---|---|
| 2026-10-05 | Esqueleto inicial: FastAPI + SQLite + React/Vite, modo stub, fórmula de puntaje | ec98db1, 39e11aa |
| 2026-10-06 | Etapa 0: auditoría, `docs/RETO.md`, `docs/AUDITORIA.md`, `.gitignore` restaurado desde `main` | 4629ffc |
| 2026-10-06 | Etapa 2–3: agente live (embeddings locales, temas, eventos, procedencia, contradicciones, contexto BM/USGS, consultas con abstención, borrador con validador, LLM con caché), UI de flujo completo, pruebas T01–T10 | cd50d3c |
| 2026-10-06 | Etapa 1: snapshot real versionado (TVN RSS + GDELT + Banco Mundial + USGS) con manifest SHA-256 | ver `git log` |
| 2026-10-06 | Etapa 4: benchmark de 60 consultas, etiquetas de temas y pares, `eval/run_eval.py` | ver `git log` |
| 2026-10-06 | Revisión de código y nueva UI: separación de patrones de inyección (fuente vs consulta), todas las fichas guardadas (las consultas abren cualquier evento), pipeline refactorizado, fecha de detección nunca presentada como publicación, UI editorial minimalista con rutas directas, `iniciar.ps1`, README | ver `git log` |
| 2026-10-06 | Etapa 5: clon limpio verificado (métricas idénticas), export Notion completo (catálogo, 7 fichas generadas, matriz T01–T10, presentación), T04 nulo determinista, `docs/AUDITORIA_FINAL.md` | ver `git log` |
| 2026-10-06 | IA generativa integrada en consultas (Claude redacta con evidencia recuperada + validador), estado de IA en la cabecera, generador visible en borradores y respuestas, `python -m app.agent.precalentar` para la caché offline, `LLM_CACHE_DIR` | ver `git log` |
| 2026-10-06 | IA generativa local y gratuita: Hermes 3 3B vía Ollama (proveedor por defecto), borrador híbrido, botón "Redactar con IA", normalización de citas de modelos pequeños, fechas en palabras en el validador | ver `git log` |
| 2026-10-07 | Agenda: URL como única fuente de verdad, cancelación de respuestas viejas, selector de cantidad con número personalizado y Máx, aviso "solo hay N", bandeja por SQL (solo las N pedidas), migración de la base, manejador de errores en JSON, borradores en curso compartidos | ver `git log` |
| 2026-10-07 | Evidencia verificable en código: validador contra el corpus (citas a registros inexistentes, campos inventados, sin sustento textual), conteo de eliminadas y citas clicables que abren el registro fuente | 1d7af7b |
| 2026-10-07 | Procedencia visible: "N notas, M procedencias independientes" | e210b8a |
| 2026-10-07 | Consulta con tres estados (respondida, abstención, contradicción lado a lado) y acción sugerida | 29c312e |
| 2026-10-07 | La consulta maneja la interfaz con acciones de una lista cerrada validada (filtrar_tema, abrir_ficha, responder, abstenerse) | b098b85 |
| 2026-10-07 | Pruebas independientes del orden y aisladas de la base real (`conftest.py`) | 970e6eb |
| 2026-10-07 | Puntaje explicado por componente y vista "¿qué pasaría si…?" sin guardar | 38d0808 |
| 2026-10-07 | Modo jurado: T01–T10 en vivo con evidencia; métricas leídas de `eval/results.json` | 195ef90 |
| 2026-10-07 | Demo robusta sin red (IA caída → caché → plantilla/abstención, nunca 500), `run_demo.ps1`, Docker (sin probar), prueba de que no hay credenciales en el repo, caché de Hermes versionada | e491581 |
| 2026-10-07 | Export a Notion generado desde el sistema (`python -m app.notion_export`) | cb90a22 |
| 2026-10-07 | UX editorial accesible: banner titular/metadatos en ficha y borrador, publicación ≠ detección, errores con acción, salto al contenido, contraste AA comprobado por prueba | a0b2822 |
| 2026-10-07 | Marca Nexo (logo, favicon, cabecera, nombre) y arreglo de la agenda con clics rápidos | 8a31b11 |
| 2026-10-07 | Pulido del backend sin cambiar resultados (reutilización, código muerto fuera, estado de consulta coherente); la evaluación da los mismos números | 1db2f21 |
| 2026-10-07 | Pulido del frontend sin cambiar la interfaz (una sola fuente para vistas/secciones/temas/pesos, componentes y arnés e2e compartidos) | 4ce1a63 |

## Pruebas fallidas y su corrección (para Notion)

| Prueba | Fallo observado | Causa | Corrección |
|---|---|---|---|
| T05 contradicciones | Las versiones "3 viviendas" y "40 viviendas" no aparecían como contradicción | El criterio de réplica (Jaccard ≥ 0,8) las trataba como la misma procedencia | Una réplica exige las mismas cifras (D08) |
| T05 (pares 2 y 5) | Titulares iguales salvo la cifra quedaban en eventos separados | Cambiar la cifra bajaba la similitud semántica bajo 0,80 | Regla léxica de agrupación sin cifras (D08) |
| Calibración del ranking | Notas internacionales de TVN (American Idol, ébola) en el top 5 | Todo TVN contaba como vínculo con Panamá = 1 y faltaban prototipos de "otros" | D07 y D09 |
| Revisión de código | Titulares legítimos ("prioridad máxima a la vacunación", "sin fuentes de agua", "Fábrica de…") se marcaban como inyección y perdían evidencia | Patrones de consulta aplicados también a fuentes | Patrones separados; prueba de regresión |
| Revisión de código | Un evento recuperado por una consulta podía no tener ficha (404) | Solo se guardaban las 60 mejores fichas | Se guardan todas; prueba de regresión |
| Revisión visual | El borrador decía "reportó el …" con la fecha de detección de GDELT | La plantilla usaba la detección como publicación | Texto explícito: "fecha de publicación no disponible; detectado por GDELT el …" |
| Prueba de consulta con IA | El validador aceptó "La economía crecerá 9% el próximo año" | El mes de la fecha de detección (septiembre = 9) contaba como cifra respaldada | Las fechas solo respaldan fechas escritas como fecha (dd/mm/aaaa, hh:mm); prueba de regresión |
| Prueba real con Hermes 3 | La 1.ª respuesta perdió todas sus frases ("sin cita") | Hermes escribió los ids dentro del texto y citó medios en vez de ids | `recuperar_citas` + ejemplo de formato en el prompt; se valida igual |
| Prueba real con Hermes 3 | Borrador completo: JSON truncado tras 228 s | Salida demasiado larga para un modelo de 3B en CPU | Modo híbrido (D17) |
| Uso real de la web | Elegir 10 y volver a 5 se quedaba en 10 | Cada clic lanzaba una petición y la última en llegar ganaba, aunque fuera la vieja | URL como fuente de verdad + `AbortController`; prueba de rutas y de prefijos consistentes |
| Uso real de la web | Casos de prueba + 5/10 daba error o se desincronizaba | Un efecto volvía a activar el interruptor al abrir una ficha sintética | Estado derivado de la URL; la ficha ya no toca el filtro |
| Uso real de la web | Error 500 al elegir 30 | No reproducible desde la API. Causas probables: backend ocupado con la IA y proxy de Vite apuntando a `localhost` (IPv6) con el backend en IPv4; el error además nunca se borraba | Proxy a `127.0.0.1`, reintento de GET, error con botón Reintentar |
| Uso real de la web | Solo 8 casos de prueba aunque se pidan 10 | Solo existen 8 sintéticos | Aviso "solo hay N", campo "otro número" y botón Máx |
| Uso real de la web | Regenerar borrador no mostraba nada | Si se cambiaba de ficha durante el minuto de generación, la respuesta tardía reemplazaba la ficha activa por otra. Además el proxy cortaba a 120 s | Respuesta tardía solo aplica si es la ficha abierta; generaciones en curso compartidas; proxy a 10 min |
| e2e en navegador | "Abrir una ficha sintética no apaga los casos de prueba" fallaba | Error del script de prueba: pedía un nodo del DOM "por valor" y CDP lo devuelve vacío; la pantalla estaba bien | `!!` en la condición; 16/16 |
| e2e en navegador | Con clics rápidos en 5/10/30, ~1 de cada 3 corridas mostraba «Esta vista tuvo un problema» | Una petición cancelada mientras se leía la respuesta se convertía en `{}` y la lista quedaba sin `items` | La cancelación se propaga en `api()`; 4 pruebas nuevas y 10/10 corridas e2e en verde (8a31b11) |
