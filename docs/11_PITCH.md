# Pitch (10 minutos, presentado desde Notion)

> Guion, demo, preguntas difíciles

## Guion

| Min | Bloque | Qué decir / mostrar |
|---|---|---|
| 0–1 | Problema y usuario | Un editor de TVN abre el día con cientos de titulares repetidos. Repetir no es confirmar. Nuestro usuario: la mesa editorial |
| 1–2 | Solución y datos | Snapshot público congelado: RSS de TVN (solo metadatos), GDELT, Banco Mundial y USGS. Flujo: calidad → bandeja → ficha → borrador → revisión. Nada se publica solo |
| 2–6 | Demo en vivo (sin internet) | (1) Reporte de calidad. (2) Bandeja top 5 con barras R, I, U, N, E. (3) Ficha de un tema económico: quién lo reporta, cuántas procedencias, contexto del Banco Mundial con año y unidad, qué falta. (4) Generar borrador: cada afirmación con tipo y cita; mostrar afirmaciones eliminadas por el validador. (5) Revisión: intentar aprobar un tema con evidencia insuficiente → bloqueado. (6) Consulta "¿Cuál es la inflación de Panamá hoy?" → abstención. (7) Casos sintéticos: inyección con E = 0 y contradicción con ambas versiones |
| 6–8 | IA, baseline y métricas | Embeddings multilingües locales para temas, eventos y búsqueda. Comparación con palabras clave y ranking por fecha. Leer la tabla de `eval/resultados/REPORTE.md` con numerador/denominador y fallos |
| 8–9 | Valor | Hipótesis de valor (no medida): menos tiempo para encontrar un tema investigable y saber qué falta verificar. Ahorro de tiempo PENDIENTE de medir con tarea manual vs asistida |
| 9–10 | Riesgos, límites y próximos pasos | Solo titulares; detección por patrones; etiquetas por revisar; próximos pasos: editor que valide el top 5, más fuentes primarias, lectura autorizada de textos de TVN |

## Preguntas dinámicas del jurado (respuestas preparadas)

| Pregunta | Respuesta y dónde mostrarlo |
|---|---|
| "Muéstrame de dónde proviene esta cifra y de qué año es" | Cada cifra BM lleva el id `WB:PAN:INDICADOR:AÑO` y el campo `valor`; el año y la unidad están en el texto. Abrir la ficha → Contexto oficial |
| "Si cinco medios replican la misma agencia, ¿cuántas fuentes independientes cuentas?" | Una. Mostrar el caso sintético `S-DUP` (3 titulares, 1 procedencia) y un evento real con réplicas en la tabla de titulares |
| "¿Qué ocurre si no hay evidencia o una fuente intenta cambiar instrucciones?" | Abstención explícita con qué falta; la fuente inyectada queda con E = 0 y alerta, y el validador descarta lo que no tenga cita. Mostrar `S-INY-001` y la consulta adversarial |
| "Muéstrame en Notion una decisión, una prueba fallida y su corrección" | Decisión D06 (réplica léxica); prueba fallida T05 y su corrección D08 (`docs/10_CHANGELOG.md`) |
| "¿El puntaje dice qué es verdad?" | No. Es un orden de atención. El estado de evidencia es aparte y "suficiente para el borrador" no confirma nada |
| "¿Cuánto cuesta?" | Embeddings: 0 USD (local). LLM: costo por borrador registrado en `meta_llm`; la evaluación corre en modo offline a 0 USD |
