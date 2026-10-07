# Copiloto TVN — "De la señal a la decisión"

Prototipo para la mesa editorial de TVN, hecho para el hackIAthon Panamá 2026.

## Qué es esto

Cada mañana, un editor tiene cientos de titulares de muchos medios. Muchos repiten la misma nota de agencia, otros son viejos o no tienen relación con Panamá, y casi ninguno trae el dato oficial que permite ponerlos en contexto.

El Copiloto hace ese primer filtro y deja la decisión en manos de una persona:

1. **Ordena la agenda.** Agrupa los titulares que hablan del mismo hecho, cuenta cuántas fuentes *independientes* lo reportan (cinco medios que replican a EFE cuentan como una) y calcula un puntaje de atención de 0 a 100 con una fórmula visible: P = 30·Relevancia + 25·Impacto + 20·Urgencia + 15·Novedad + 10·Evidencia.
2. **Explica cada tema en una ficha.** Qué se reporta, quién lo reporta, qué está respaldado, qué falta comprobar y qué se recomienda hacer. Si hay un dato oficial pertinente (Banco Mundial, USGS), lo agrega con país, año y unidad, y advierte que es un dato anual, no "de hoy".
3. **Redacta un borrador.** Título, enfoque, brief, preguntas de investigación, guion de TV y copy digital. Cada frase lleva su cita y su tipo (hecho, declaración, inferencia o hipótesis). Un validador en código borra cualquier frase sin respaldo o con cifras que no están en la fuente.
4. **Deja la decisión a una persona.** Hay cinco estados de revisión con nombre de revisor y comentario. Aprobar un borrador **no publica nada**, y un tema con evidencia insuficiente no se puede aprobar.

También responde preguntas en español y **se abstiene** cuando no hay evidencia: por ejemplo, si se le pide la inflación "de hoy" o un dato que no existe. Ignora las fuentes que intentan darle órdenes (inyección de instrucciones).

**Con qué datos.** Un snapshot público congelado el 6 de octubre de 2026:

| Fuente | Contenido |
|---|---|
| RSS de TVN | 152 titulares; solo título, URL y fecha |
| GDELT | 723 titulares de otros medios |
| Banco Mundial | 6 países × 6 indicadores × 2010–2024 |
| USGS | 82 sismos de 2024 en la región |

Todo funciona **sin internet** durante la demo.

**Dónde está la IA.**
- **Embeddings multilingües locales** (ONNX, sin GPU). Clasifican en 6 temas, agrupan titulares del mismo hecho aunque estén en otro idioma y buscan por significado.
- **Hermes 3, local y gratuito, vía Ollama.** Redacta respuestas a consultas y la parte editorial de los borradores (título, enfoque, preguntas y copy), siempre a partir de la evidencia recuperada y pasando por un validador de citas. Sin el modelo usa respuestas en caché o una plantilla determinista.
- **Comparación con un baseline.** El agente se compara con una búsqueda por palabras clave y un ranking por fecha. Ver [docs/07_EVALUATION.md](docs/07_EVALUATION.md).

## Cómo encenderlo

Requisitos: Windows con PowerShell, **Python 3.12 o 3.13**, **Node.js 18 o superior** y, para la IA generativa, **Ollama** con `hermes3:3b` (ver más abajo).

### Opción rápida (un comando)

Desde la carpeta del repo, en PowerShell:

```powershell
# La primera vez: instala dependencias, descarga el modelo (~0,22 GB) y enciende
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar

# Las siguientes veces: solo enciende
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

Se abren dos ventanas de PowerShell (backend e interfaz) y el navegador en **http://localhost:5173**. Para apagar, cierra esas dos ventanas.

### Opción manual

```powershell
Copy-Item .env.example .env

# Backend (una vez)
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m app.agent.embed --descargar
cd ..

# Interfaz (una vez)
cd frontend
npm install
cd ..

# Encender — Terminal 1
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000

# Encender — Terminal 2
cd frontend
npm run dev
```

Abre **http://localhost:5173**. La documentación de la API está en http://localhost:8000/docs.

### IA generativa local y gratuita: Hermes 3 con Ollama

La app usa **Hermes 3** (Nous Research, 3B parámetros), que corre en tu equipo con **Ollama**. Es gratuito, no necesita clave y funciona sin internet. Instálalo una vez:

```powershell
winget install --id Ollama.Ollama -e     # instala Ollama
ollama pull hermes3:3b                   # descarga Hermes 3 (~2 GB)
```

`iniciar.ps1` y el backend lo detectan solos (`LLM_PROVIDER=ollama`, `LLM_MODEL=hermes3:3b` en `.env`). En la cabecera, el indicador **IA** se pone verde con el nombre del modelo.

**Qué hace Hermes en la app**

| Lugar | Qué redacta | Cómo se controla |
|---|---|---|
| Consultar | Botón **"Redactar respuesta con IA"** sobre los titulares encontrados | Cada frase debe citar una evidencia real |
| Borrador | Título, enfoque de interés público, 3 preguntas de investigación y copy digital | El brief y el guion con los hechos y las cifras los arma el código, con sus citas |

Todo lo que escribe la IA pasa por el **validador de citas**. Se elimina cualquier frase sin cita válida, con cifras o fechas que no estén en la fuente, o con instrucciones inyectadas. La interfaz muestra qué escribió la IA y qué descartó el validador.

**Velocidad.** En un portátil sin GPU, Hermes tarda alrededor de 1 minuto por respuesta o borrador. La interfaz muestra un contador mientras trabaja. Lo ya generado queda en caché (`data/cache/llm/`) y sale al instante. Para la demo, precalienta la caché antes (tarda unos 30–40 min la primera vez):

```powershell
cd backend
.\.venv\Scripts\python -m app.agent.precalentar --top 5
cd ..
git add data/cache/llm; git commit -m "data: cache Hermes para demo offline"; git push origin feat/agente
```

**Otros proveedores (opcional).** En `.env` puedes cambiar `LLM_PROVIDER` a `openai`, para APIs compatibles como Kimi (Moonshot) o Groq, usando `LLM_BASE_URL` y `LLM_API_KEY`. También puedes usar `anthropic` (Claude) con `LLM_API_KEY`. Sin ningún modelo disponible, el sistema usa la caché o una plantilla determinista: nunca se cae.

## Recorrido por la interfaz

| Pestaña | Qué muestra |
|---|---|
| **Agenda** | Top 5, 10 o 30 temas. Cada uno muestra el puntaje (rojo = prioridad alta), el estado de evidencia y una barra con los 5 componentes. Al abrir un tema aparece su ficha con las sub-pestañas **Ficha**, **Fuentes**, **Puntaje**, **Borrador** y **Revisión**. La casilla "Ver casos de prueba" muestra los casos sintéticos: inyección, contradicciones, noticia antigua y agencia replicada |
| **Consultar** | Preguntas en español con ejemplos listos, incluida una abstención y un intento de inyección |
| **Datos** | Reporte de calidad del snapshot, catálogo con SHA-256 y límites de cobertura |
| **Evaluación** | Métricas del agente frente al baseline, con numerador y denominador |

Las horas se muestran en hora de Panamá. La "antigüedad" se mide contra la fecha de corte del snapshot, no contra el reloj, para que la demo sea reproducible.

**Enlaces directos** (útiles para el pitch o para Notion):

- `http://localhost:5173/#/ficha/SINT-S-CON-001/resumen` abre un caso con versiones incompatibles.
- `http://localhost:5173/#/ficha/SINT-S-INY-001/resumen` abre una fuente que intenta dar órdenes al sistema.
- `http://localhost:5173/#/consulta?q=¿Cuál es la inflación de Panamá hoy?` muestra una abstención.
- `http://localhost:5173/#/evaluacion` abre las métricas.

## Pruebas y evaluación

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q             # pruebas T01–T10 del reto y regresiones
cd ..
backend\.venv\Scripts\python eval\run_eval.py   # agente vs baseline → eval\resultados\
```

Las etiquetas del benchmark las propuso un asistente de IA y están **pendientes de revisión humana**. Ver [docs/07_EVALUATION.md](docs/07_EVALUATION.md).

## Datos

El snapshot está versionado en `data/raw/` con `manifest.json` (SHA-256, consultas, fecha de corte). Regenerarlo requiere internet y cambia los resultados:

```powershell
python data\scripts\download_snapshot.py all
python data\scripts\validate.py
```

| Archivo | Contenido |
|---|---|
| `data/raw/noticias.csv` | TVN RSS (solo título, URL, fecha) + GDELT DOC 2.0 |
| `data/raw/indicadores.csv` | Banco Mundial: 6 países × 6 indicadores × 2010–2024 |
| `data/raw/eventos.geojson` | USGS: sismos 2024, M ≥ 3, caja lat 5–12, lon −86/−76 |
| `data/synthetic/casos_controlados.csv` | Casos de prueba sintéticos rotulados |
| `data/processed/` | Noticias válidas y con error, reporte de calidad, `fichas.jsonl`, caché de embeddings |
| `eval/benchmark.jsonl` | 60 consultas (40 dev / 20 reservadas) |

Diccionario, licencias y desviaciones del PDF: [docs/06_DATASET.md](docs/06_DATASET.md).

## Si algo falla

| Síntoma | Solución |
|---|---|
| La interfaz dice "No hay conexión con el backend" | El backend no está encendido o no está en el puerto 8000 |
| Aviso "modelo local no disponible" en el backend | Falta el modelo: `backend\.venv\Scripts\python -m app.agent.embed --descargar`. Mientras tanto se usa un respaldo léxico de menor calidad |
| Quiero empezar de cero las revisiones | Borra `data\app.db` y reinicia el backend |
| `iniciar.ps1` no se ejecuta | Úsalo con `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1` |

## Estructura

```
backend/app/agent/   IA: embeddings, temas, eventos, contexto, puntaje, consultas, borradores, seguridad, baseline
backend/app/         API FastAPI, SQLite, fórmula de puntaje
backend/tests/       pruebas T01–T10 y regresiones
frontend/src/        interfaz (App.jsx, views/, lib.js, style.css)
data/                snapshot, scripts de descarga y validación, casos sintéticos
eval/                benchmark, etiquetas y evaluación
docs/                documentación (01–12) y export para Notion (docs/notion_export/)
iniciar.ps1          instala y enciende todo en Windows
```
