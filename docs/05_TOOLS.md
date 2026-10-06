# Herramientas

> Tools, parámetros permitidos, límites

El agente no usa herramientas autónomas ni ejecuta acciones: es un flujo fijo controlado por código. El LLM solo redacta texto a partir de un bloque de datos y su salida pasa por un validador.

| Componente | Entrada | Salida | Límites |
|---|---|---|---|
| `download_snapshot.py` | `wb`, `usgs`, `news`, `all` | `data/raw/*` + manifest | Necesita internet. GDELT: 250 artículos por consulta, ≥ 5 s entre llamadas, reintentos con espera |
| `validate.py` | carpeta raw y processed | CSV válidos/errores + reporte | No bloquea la carga; no rellena nulos |
| Embeddings | titulares | vectores 384-d | Modelo local `paraphrase-multilingual-MiniLM-L12-v2`; sin modelo usa n-gramas |
| `query.responder` | pregunta 3–500 caracteres | QueryOut | Solo responde con evidencia; umbral de similitud 0,45 |
| `draft.generar` | ficha | borrador | Brief ≤ 250, copy ≤ 80, guion 45–60 s estimado a 2,5 palabras/s |
| LLM (Claude) | system + `<DATOS>` | JSON por esquema | `LLM_MODEL` (por defecto `claude-opus-5-5`), `LLM_EFFORT=low`, `max_tokens=8000`, timeout 60 s, 1 reintento |
| `run_eval.py` | benchmark y etiquetas | métricas | Por defecto sin LLM (costo 0) |

**Parámetros configurables** (`.env`): `AGENT_MODE`, `DATA_DIR`, `TVN_RSS_URL`, `NEWS_DAYS`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_EFFORT`, `LLM_OFFLINE`, `SIM_CLUSTER`, `SIM_QUERY_MIN`, `EMB_MODEL`.
