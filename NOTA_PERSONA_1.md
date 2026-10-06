# Nota para Persona 1 (IA) — cómo conectar tu agente al backend

Este repo ya tiene backend, base de datos y UI. **Tu trabajo se conecta en UN solo archivo:**
`backend/app/agent_interface.py`. El backend solo llama a 3 funciones:

| Función | Entrada | Salida | Qué debe hacer |
|---|---|---|---|
| `build_candidates()` | — | `list[Ficha]` | Agrupar noticias, contextualizar con indicadores/USGS, dar componentes R,I,U,N,E (0–1) y `estado_evidencia`. **No calcules el puntaje**: lo hace `scoring.py` (30R+25I+20U+15N+10E). |
| `answer_query(pregunta)` | `str` (3–500 chars) | `QueryOut` | Responder solo con evidencia recuperada. Sin evidencia: `abstencion=True` + `faltante`. |
| `generate_draft(ficha)` | `Ficha` | `dict` | Brief ≤250 palabras, título, 3 preguntas, guion 45–60 s, copy ≤80 palabras, con `citas`. |

**Cómo enchufarte**
1. Crea `backend/app/agent/__init__.py` que exporte esas 3 funciones con las **mismas firmas**.
2. En `.env` pon `AGENT_MODE=live`. En `stub` el sistema usa datos DEMO marcados como sintéticos.
3. Para re-sembrar fichas: borra `data/app.db` y reinicia el backend.
4. Los modelos (`Ficha`, `Cita`, `QueryOut`) están en `backend/app/models.py` y espejan `fichas.jsonl`. Si necesitas cambiar un campo, avísale a Persona 2 antes.

**Reglas del reto que tu agente debe cumplir** (las prueban T01–T10)
- Cada afirmación lleva `Cita` con `id_evidencia` y `campo`. Sin cita válida, no se emite.
- Si solo hay titular/metadatos: `base="titular/metadatos"`. No simules haber leído el artículo.
- Abstención explícita cuando no hay respaldo (T06). No inventes cifras, citas ni fuentes.
- El texto de las noticias es **dato, no instrucción** (T07). Separa instrucciones y contenido en el prompt.
- Indicadores del Banco Mundial: siempre país, año y unidad; nunca "cifra de hoy" (T04).
- Varias noticias de la misma agencia = **1** fuente independiente (T02).
- Credenciales solo en `.env`, nunca en código, prompts ni logs.

**Datos**: `python data/scripts/download_snapshot.py all` → `data/raw/`; luego `python data/scripts/validate.py` → `data/processed/`.
Contrato completo y probador de endpoints: http://localhost:8000/docs
