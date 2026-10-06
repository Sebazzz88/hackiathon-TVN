# Diseño de solución

- **Arquitectura y modelo de datos:** ver `docs/03_ARCHITECTURE.md` (pegar el diagrama como bloque de código en Notion).
- **Reglas y componentes del puntaje:** ver `docs/04_AGENT.md` § Componentes. Versión de reglas `reglas-v1`; pesos 30/25/20/15/10.
- **Modelos:**

| Uso | Modelo / proveedor | Versión | Parámetros | Costo |
|---|---|---|---|---|
| Embeddings (clasificación, agrupación, búsqueda) | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` vía fastembed (ONNX, local) | fastembed 0.8.1 | 384 dimensiones, sin GPU | 0 USD |
| Redacción de borradores (opcional) | Claude, Anthropic | `claude-opus-5-5` (configurable) | effort=low, max_tokens=8000, salida JSON por esquema | Medido por borrador en `meta_llm.costo_usd`; 0 USD en la evaluación (modo offline) |

- **Prompts:** sistema `draft-v1` y formato `<DATOS>` en `docs/04_AGENT.md`; texto exacto en `backend/app/agent/draft.py`.
- **Límites del sistema:** solo titulares/metadatos; detección de agencia e inyección por patrones; contradicciones solo numéricas; sin monitoreo continuo; ver `docs/04_AGENT.md` § Límites.
