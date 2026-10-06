# Evaluación

> Baseline vs agente, métricas reales, errores

Ejecución: `backend\.venv\Scripts\python eval\run_eval.py` (2026-10-06 21:58 UTC). Salidas guardadas en `eval/resultados/` (`resumen.json`, `detalle_dev.jsonl`, `detalle_reservado.jsonl`, `REPORTE.md`, `afirmaciones_para_revision.csv`). Entorno: CPU local Windows, embeddings ONNX locales, LLM desactivado (plantilla determinista). Costo: 0 USD.

## Advertencias antes de leer los números

1. **Las etiquetas son propuestas por el asistente de IA (Claude) y están PENDIENTES de revisión humana.** Las métricas son preliminares hasta que una persona las revise.
2. **El conjunto reservado no es ciego.** Las 60 consultas las redactó el mismo asistente que construyó el sistema. El 100% del reservado es optimista y no sustituye el set reservado del jurado.
3. **Los umbrales se ajustaron solo con el conjunto dev** (40 consultas). El reservado se ejecutó una vez, sin cambios posteriores.
4. Las 10 consultas de contradicción usan noticias sintéticas rotuladas (`data/synthetic/`).

## Baselines

| Tarea | Baseline | Agente (IA) |
|---|---|---|
| Consultas | Búsqueda por palabras clave sobre titulares; responde con el primer resultado o se abstiene si no hay palabras en común | Indicadores estructurados + recuperación semántica + abstención + detección de inyección |
| Clasificación | Reglas de palabras clave por tema | Similitud de embeddings a prototipos con umbral |
| Agrupación | Jaccard de palabras ≥ 0,5 | Similitud de embeddings ≥ 0,80 en ventana de 5 días + regla léxica |
| Ranking | Más reciente primero | P = 30R + 25I + 20U + 15N + 10E |

## Resultados

| Métrica | Agente | Baseline | Nota |
|---|---|---|---|
| [dev] Respuestas sustentadas correctas | 20/20 | 6/20 | Antes de corregir: 17/20 (ver "Fallos corregidos") |
| [dev] Contradicciones mostradas | 7/7 | 0/7 | Antes: 6/7 |
| [dev] Abstención correcta (sin respuesta + adversarial) | 13/13 | 2/13 | Antes: 11/13. Meta ≥ 80% |
| [dev] Abstención incorrecta en respondibles | 0/27 | 1/27 | |
| [reservado] Respuestas sustentadas correctas | 10/10 | 5/10 | Una sola ejecución |
| [reservado] Contradicciones mostradas | 3/3 | 0/3 | |
| [reservado] Abstención correcta | 7/7 | 0/7 | |
| [reservado] Abstención incorrecta en respondibles | 0/13 | 0/13 | |
| Cobertura de citas en borradores | 195/195 | — | 18 borradores. 2 afirmaciones eliminadas por el validador, ambas del caso de inyección |
| Validez de sustento | PENDIENTE | — | Requiere revisión humana de ≥ 30 filas de `afirmaciones_para_revision.csv` |
| Clasificación macro-F1, dev (n = 100) | 0,568 | 0,547 | Exactitud 83/100 frente a 78/100 |
| Clasificación macro-F1, test (n = 50) | 0,440 | 0,395 | Exactitud 39/50 frente a 41/50 |
| Agrupación de eventos, F1 (60 pares) | 0,875 | 0,615 | Agente: precisión 14/15, recall 14/17 |
| Precision@5 | PENDIENTE | — | Falta la selección independiente de un editor |
| Tiempo por consulta, mediana / p95 | 0,005 s / 0,015 s | — | Meta ≤ 15 s. Pipeline completo 4,9 s (con caché de embeddings) |
| Guion 45–60 s (plantilla) | 9/18 | — | Con una sola fuente no hay material verificable para 45 s; el sistema lo avisa en vez de rellenar |

## Qué aporta la IA y cuándo no ayuda

- **Ayuda mucho en consultas.** Recupera eventos aunque la pregunta use otras palabras o el titular esté en otro idioma, y se abstiene cuando nada se parece. El baseline responde con cualquier coincidencia de palabras y nunca detecta inyecciones ni contradicciones.
- **Ayuda en agrupación.** Une titulares del mismo hecho en español, inglés y alemán (F1 0,875 frente a 0,615).
- **Casi no ayuda en clasificación temática con titulares.** El macro-F1 mejora poco y en test la exactitud es menor. La muestra aleatoria es 75% "otros" (el RSS de TVN trae muchas notas institucionales), así que las clases temáticas tienen 1 a 5 ejemplos en test y la métrica es inestable. Errores típicos: la "S & P ratifica grado de inversión" queda en "otros" por el umbral de margen; notas culturales caen en "turismo".
- **El ranking no se puede validar sin un editor.** El top 5 del agente prioriza Canal, Sinaproc, AMP, sismo y Moody's. El baseline por fecha pone primero "Príncipes de Gales" y la vigilancia de peste en Rusia. Es exploratorio.

## Fallos encontrados en dev y corregidos (registrar en Notion)

| Caso | Fallo | Causa | Corrección |
|---|---|---|---|
| B05 | "porcentaje de la población que usaba internet" respondió población | Primer indicador que coincidía | Orden de lo específico a lo general |
| B06 | "exportaciones en el PIB" respondió crecimiento del PIB | Igual | Igual |
| B20, B37 | "precio de la gasolina/diésel" respondió inflación del BM | "precio" activaba el IPC | En consultas, "precio" solo no activa inflación |
| B47 | "inflación el próximo año" dio el dato de 2024 | No se detectaban pronósticos | "próximo año", "será", "pronóstico" → abstención |
| B45 | Cricket recuperó béisbol | Umbral 0,45 bajo | Umbral 0,55: en dev, sin respuesta ≤ 0,47 y respondibles ≥ 0,61 |
| T05 | Contradicción oculta | Réplica sin comparar cifras | D08 |
| Plantilla | "20 mil" escrito como "20000" eliminado por el validador | Formato de cifra | La plantilla cita el titular textual |

## Errores restantes del agente

- **Agrupación:** une dos notas institucionales distintas de TVN Media (falso positivo) y separa "Transición de mando en el Canal" de la nota alemana sobre la primera administradora (falso negativo).
- **Clasificación (test):** 11 errores. Ver `eval/resultados/REPORTE.md`.

## Pendientes para cerrar la evaluación

1. Revisión humana de etiquetas: `eval/etiquetas_temas.csv`, `eval/etiquetas_pares.csv` y `eval/benchmark.jsonl` (columna `revisado_por`).
2. Validez de sustento: marcar ≥ 30 filas en `eval/resultados/afirmaciones_para_revision.csv`.
3. Precision@5: un editor elige 5 temas sin ver el ranking y se guarda en `eval/seleccion_editor.json` como `{"ids": ["EV-…", …]}`.
4. Ahorro de tiempo: no medido. Requiere una tarea manual frente a asistida con número de pruebas declarado.
