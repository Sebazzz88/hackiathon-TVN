<p align="center"><img src="assets/nexo_dark.png" alt="Nexo · Copiloto editorial" width="330"></p>

# Nexo · Copiloto editorial para TVN — "De la señal a la decisión"

<div align="center">

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![CSS](https://img.shields.io/badge/CSS-663399?style=flat-square&logo=css&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?style=flat-square&logo=powershell&logoColor=white)](https://learn.microsoft.com/powershell/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-000000?style=flat-square)](https://ollama.com/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

</div>

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

## Demo

### 1. Agenda editorial

La vista principal organiza los temas detectados y prioriza la agenda según relevancia, impacto, urgencia, novedad y evidencia.

![Demo - Agenda](assets/demo/01-agenda.gif)

### 2. Investigación

Cada tema se puede abrir para revisar qué se sabe, qué fuentes lo respaldan, qué falta comprobar y qué acciones de investigación se recomiendan.

![Demo - Investigación](assets/demo/02-investigacion.gif)

### 3. Consultar

El editor puede hacer preguntas en lenguaje natural y recibir respuestas construidas a partir de la evidencia disponible. Cuando los datos no permiten responder con seguridad, Nexo se abstiene.

![Demo - Consultar](assets/demo/03-consultar.gif)

### 4. Datos

La sección de datos permite consultar el snapshot utilizado por el sistema, su cobertura y la información proveniente de TVN, GDELT, Banco Mundial y USGS.

![Demo - Datos](assets/demo/04-datos.gif)

### 5. Evaluación

El sistema permite ejecutar y revisar las pruebas de aceptación, contrastar los resultados del agente con el baseline y observar la evidencia utilizada para cada evaluación.

![Demo - Evaluación](assets/demo/05-evaluacion.gif)

## Paso a paso: dejarlo funcionando desde cero

Todos los comandos son de **PowerShell** en Windows 10 u 11. Necesitas unos 5 GB libres y conexión a internet **solo la primera vez** (después todo corre sin internet).

### 1. Instala los programas base (una sola vez)

Verifica si ya los tienes:

```powershell
git --version
python --version     # debe ser 3.12 o 3.13
node --version       # debe ser 18 o superior
```

Si falta alguno, instálalo con winget (después **cierra y vuelve a abrir PowerShell**):

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.13 -e
winget install --id OpenJS.NodeJS.LTS -e
```

### 2. Descarga el proyecto

```powershell
git clone https://github.com/Sebazzz88/hackiathon-TVN.git
cd hackiathon-TVN
```

### 3. Instala todo y enciéndelo con un solo comando

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar
```

Este comando hace, en orden:

| Paso | Qué hace | Tarda (primera vez) |
|---|---|---|
| 1 | Crea `.env` a partir de `.env.example` | segundos |
| 2 | Crea el entorno de Python e instala las dependencias | 2–4 min |
| 3 | Descarga el modelo de embeddings multilingüe (~0,22 GB) | 1–2 min |
| 4 | Instala la interfaz (Node) | 1–2 min |
| 5 | Instala **Ollama** y descarga **Hermes 3** (~2 GB) | 5–10 min |
| 6 | Enciende backend e interfaz, y abre el navegador | ~20 s |

Al final verás `Backend listo. IA generativa conectada: hermes3:3b` y se abrirá **http://localhost:5173**. Se quedan abiertas dos ventanas de PowerShell (backend e interfaz): **no las cierres mientras uses la app**.

### 4. Comprueba que todo quedó funcional

1. En la cabecera de la página, el indicador **IA hermes3:3b · local** debe estar en verde.
2. Pestaña **Agenda**: aparece el top 5 y una ficha a la derecha. El primero es "Canal de Panamá: Suspensión temporal de operaciones de potabilizadora de Miraflores".
3. Pestaña **Datos**: 875 noticias válidas, 152 de TVN, 540/540 celdas del Banco Mundial y 82 sismos.
4. Pestaña **Consultar**: pulsa el ejemplo "¿Cuál es la inflación de Panamá hoy?". Debe **abstenerse** y explicar que solo hay datos anuales.
5. (Opcional) Corre las pruebas: deben pasar todas.

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q
cd ..
```

### 5. Uso diario

```powershell
# Encender (lo de siempre; ya no necesita -Instalar)
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1

# Apagar backend e interfaz
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Apagar
```

**Modo demo (recomendado para presentar): un comando, una ventana, un puerto.** El backend sirve también la interfaz
compilada en **http://localhost:8000**. Sin login ni credenciales. Se apaga con Ctrl+C en la misma ventana.

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1            # con Hermes si Ollama está encendido
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Offline   # 100 % sin red: caché de la IA, plantilla o abstención
```

Si la IA falla a mitad de la demo, el sistema no muestra pantallas de error: usa la caché, luego la plantilla
determinista y, si no hay evidencia, una abstención que dice qué falta y qué hacer.

Alternativa con Docker (`docker compose up --build` → http://localhost:8000). **PENDIENTE: no probado** en el equipo de
desarrollo (no tiene Docker); la ruta verificada es `run_demo.ps1`.

**Copia en línea (respaldo): https://hackiathon-tvn.vercel.app** — la misma app en Vercel (`index.py`, `vercel.json`,
`.vercelignore`), sin login. Diferencias con la demo local: la IA generativa funciona solo con la caché de Hermes o la
plantilla (no hay Ollama en la nube), y las revisiones se guardan en `/tmp`, así que **no son permanentes**: se pierden
cuando Vercel apaga la instancia. Para volver a publicar: `vercel deploy --prod` desde la raíz del repo (la función
pesa ~300 MB, por eso el proyecto tiene `VERCEL_SUPPORT_LARGE_FUNCTIONS=1`).

### Si algo falla

| Síntoma | Causa y solución |
|---|---|
| `iniciar.ps1` no se ejecuta | Usa exactamente el comando con `-ExecutionPolicy Bypass` y estando en la carpeta del proyecto |
| `python` o `node` no se reconocen | Instala el programa (paso 1) y abre una PowerShell **nueva** |
| La página dice "No hay conexión con el backend" | El backend no arrancó. Mira la ventana "Nexo - backend". Si el puerto 8000 está en uso, corre `-Apagar` y vuelve a encender |
| Indicador de IA en amarillo ("solo embeddings") | Ollama no está encendido o falta el modelo. Corre `.\iniciar.ps1` (lo enciende y lo descarga) o manualmente `ollama pull hermes3:3b` |
| Aviso "modelo local no disponible" en el backend | Falta el modelo de embeddings: `backend\.venv\Scripts\python -m app.agent.embed --descargar`. Mientras tanto usa un respaldo de menor calidad |
| La IA tarda mucho | Normal sin GPU: ~1 minuto por respuesta. Lo ya generado queda en caché y sale al instante |
| Quiero borrar mis revisiones | Apaga la app, borra `data\app.db` y enciéndela de nuevo |
| No quiero usar IA generativa | Pon `LLM_OFFLINE=1` en `.env`. Todo funciona con caché y plantilla |

### Instalación manual (alternativa al script)

```powershell
Copy-Item .env.example .env

cd backend
py -3.13 -m venv .venv                 # o: python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m app.agent.embed --descargar
cd ..\frontend
npm install
cd ..

winget install --id Ollama.Ollama -e   # IA generativa local (opcional)
ollama pull hermes3:3b

# Terminal 1: backend
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
# Terminal 2: interfaz
cd frontend
npm run dev
```

La documentación interactiva de la API está en http://localhost:8000/docs.

### IA generativa local y gratuita: Hermes 3 con Ollama

La app usa **Hermes 3** (Nous Research, 3B parámetros), que corre en tu equipo con **Ollama**. Es gratuito, no necesita clave y funciona sin internet. `iniciar.ps1 -Instalar` lo instala y lo descarga solo.

| Lugar | Qué redacta Hermes | Cómo se controla |
|---|---|---|
| Consultar | Botón **"Redactar respuesta con IA"** sobre los titulares encontrados | Cada frase debe citar una evidencia real |
| Borrador | Título, enfoque de interés público, 3 preguntas de investigación y copy digital | El brief y el guion con los hechos y las cifras los arma el código, con sus citas |

Todo lo que escribe la IA pasa por el **validador de citas**. Se elimina cualquier frase sin cita válida, con cifras o fechas que no estén en la fuente, o con instrucciones inyectadas. La interfaz muestra qué escribió la IA y qué descartó el validador.

**Demo sin internet: precalienta la caché.** Genera con Hermes los borradores y respuestas de la demo y los guarda en `data/cache/llm/` (tarda 30–40 min la primera vez):

```powershell
cd backend
.\.venv\Scripts\python -m app.agent.precalentar --top 5
cd ..
git add data/cache/llm; git commit -m "data: cache Hermes para demo offline"; git push origin main
```

**Otros proveedores (opcional).** En `.env`, `LLM_PROVIDER=openai` sirve para APIs compatibles como Kimi (Moonshot) o Groq, con `LLM_BASE_URL` y `LLM_API_KEY`. `LLM_PROVIDER=anthropic` usa Claude con `LLM_API_KEY`. Sin ningún modelo disponible, el sistema usa la caché o una plantilla determinista: nunca se cae.

## Recorrido por la interfaz

| Pestaña | Qué muestra |
|---|---|
| **Agenda** | Top 5, 10 o 30 temas, otro número a elección o **Máx** (todos). «¿Qué pasaría si…?» reordena con otros pesos sin guardar nada. Cada uno muestra el puntaje (rojo = prioridad alta), el estado de evidencia y una barra con los 5 componentes. Al abrir un tema aparece su ficha con las sub-pestañas **Ficha**, **Fuentes**, **Puntaje**, **Borrador** y **Revisión**. La casilla "Ver casos de prueba" muestra los casos sintéticos: inyección, contradicciones, noticia antigua y agencia replicada |
| **Consultar** | Preguntas en español con ejemplos listos, incluida una abstención y un intento de inyección |
| **Datos** | Reporte de calidad del snapshot, catálogo con SHA-256 y límites de cobertura |
| **Evaluación** | Métricas del agente frente al baseline, con numerador y denominador |
| **Modo jurado** | Botón «Correr T01–T10 ahora»: ejecuta las pruebas de aceptación en vivo (~10 s, sin red) y muestra verde/rojo con la evidencia de cada una. Tabla agente vs baseline leída de `eval/results.json` y atajos a las preguntas típicas del jurado |

Las horas se muestran en hora de Panamá. La "antigüedad" se mide contra la fecha de corte del snapshot, no contra el reloj, para que la demo sea reproducible.

**Enlaces directos** (útiles para el pitch o para Notion):

- `http://localhost:5173/#/ficha/SINT-S-CON-001/resumen` abre un caso con versiones incompatibles.
- `http://localhost:5173/#/ficha/SINT-S-INY-001/resumen` abre una fuente que intenta dar órdenes al sistema.
- `http://localhost:5173/#/consulta?q=¿Cuál es la inflación de Panamá hoy?` muestra una abstención.
- `http://localhost:5173/#/evaluacion` abre las métricas.
- `http://localhost:5173/#/jurado` abre el Modo jurado.

Con `run_demo.ps1` los mismos enlaces funcionan cambiando `5173` por `8000`.

## Pruebas y evaluación

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q             # pruebas T01–T10 del reto y regresiones
cd ..
backend\.venv\Scripts\python eval\run_eval.py   # agente vs baseline → eval\resultados\ y eval\results.json

cd frontend
npm test                                        # rutas, puntaje, fechas y contraste de colores (Node)
# Con la app encendida (por defecto en :5173; para run_demo usa $env:APP_URL="http://localhost:8000"):
node e2e\agenda.e2e.mjs                         # navegador real sin ventana: 5/10/30, casos de prueba, clics rápidos
node e2e\funciones.e2e.mjs                      # Máx, otro número, regenerar borrador, citas, Modo jurado, accesibilidad
cd ..
```

**Páginas de Notion generadas desde el sistema** (matriz T01–T10 observada, catálogo, fichas y bitácora de revisiones):

```powershell
cd backend
.\.venv\Scripts\python -m app.notion_export --correr   # escribe docs\notion_export\05, 10, 11 y 12
cd ..
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

## Estructura

```
backend/app/agent/   IA: embeddings, temas, eventos, contexto, puntaje, consultas, borradores, seguridad, baseline
backend/app/         API FastAPI, SQLite, fórmula de puntaje
backend/tests/       pruebas T01–T10 y regresiones
frontend/src/        interfaz (App.jsx, views/, lib.js, style.css)
data/                snapshot, scripts de descarga y validación, casos sintéticos
eval/                benchmark, etiquetas y evaluación
docs/                documentación (01–12) y export para Notion (docs/notion_export/)
iniciar.ps1          instala, enciende y apaga todo en Windows (incluye Ollama + Hermes 3)
```
