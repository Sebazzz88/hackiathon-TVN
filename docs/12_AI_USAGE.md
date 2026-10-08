# Uso de IA

> Herramienta, propósito, prompt, resultado, iteraciones

Registro honesto de las herramientas de IA usadas para construir el proyecto. La IA **dentro** del producto está en [04_AGENT.md](04_AGENT.md).

## Claude Code (Anthropic) — desarrollo principal

| Campo | Detalle |
|---|---|
| Propósito | Auditoría del repo, descarga y validación del snapshot, implementación del agente (`backend/app/agent/`), interfaz, pruebas T01–T10, benchmark, evaluación y documentación |
| Prompt principal | Instrucción por etapas (0 auditoría, 1 datos reales, 2 IA, 3 interfaz, 4 evaluación, 5 entrega) con reglas fijas del proyecto (archivo de instrucciones local, no versionado): no inventar métricas, marcar VERIFICADO/PENDIENTE, tests antes de cada commit |
| Resultado | Código y documentos en la rama `main` (desarrollado en `feat/agente` y fusionado el 2026-10-07). Cada etapa con commit y `pytest` en verde |
| Iteraciones relevantes | (1) El primer umbral de réplica por similitud semántica fusionaba titulares distintos; se midió y se cambió a criterio léxico (D06). (2) La prueba T05 detectó que dos titulares con cifras distintas se marcaban como réplica; se corrigió (D08). (3) Clasificación con margen mínimo tras ver notas internacionales en "economía" (D07). (4) Relevancia de TVN ajustada (D09) |
| Límites | Las etiquetas del benchmark y de temas fueron **propuestas por Claude** y requieren revisión humana antes de tomarse como resultados |

## IA dentro del producto (no es herramienta de desarrollo)

- Embeddings: `paraphrase-multilingual-MiniLM-L12-v2` (ONNX local).
- Generación: Hermes 3 3B (Nous Research) vía Ollama, local y gratuito. Detalle en `04_AGENT.md`.

## Codex (OpenAI)

| Campo | Detalle |
|---|---|
| Propósito | PENDIENTE: completar por el autor si se usó (p. ej., esqueleto inicial o revisión de código) |
| Prompt | PENDIENTE |
| Resultado | PENDIENTE |

## ChatGPT (OpenAI)

| Campo | Detalle |
|---|---|
| Propósito | PENDIENTE: completar por el autor (p. ej., lectura del reto, ideas de pitch) |
| Prompt | PENDIENTE |
| Resultado | PENDIENTE |

> No se registran aquí usos que no consten. El autor debe completar Codex y ChatGPT con lo que realmente hizo.
