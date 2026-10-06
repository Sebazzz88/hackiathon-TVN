# Copiloto TVN — "De la señal a la decisión" (hackIAthon Panamá 2026)

Prototipo para la mesa editorial de TVN. Convierte noticias públicas e indicadores oficiales en una bandeja de temas priorizados, fichas de evidencia y borradores con cita por afirmación, siempre sujetos a revisión humana. **Nada se publica automáticamente.**

- Reto: [docs/RETO.md](docs/RETO.md) · Producto: [docs/01_PRODUCT.md](docs/01_PRODUCT.md) · Agente: [docs/04_AGENT.md](docs/04_AGENT.md) · Evaluación: [docs/07_EVALUATION.md](docs/07_EVALUATION.md)
- Stack: FastAPI + SQLite + React/Vite. IA local: embeddings multilingües ONNX (fastembed). LLM opcional: Claude (SDK oficial), con caché y plantilla de respaldo.

## Requisitos

- Windows con PowerShell, Python 3.12 o 3.13, Node.js 18 o superior, Git.
- Internet solo para la instalación y para descargar el modelo de embeddings (una vez, ~0,22 GB). La demo funciona sin internet.

## Instalación (PowerShell, desde la raíz del repo)

```powershell
Copy-Item .env.example .env          # luego edita .env si tienes clave LLM (opcional)
cd backend
py -3.13 -m venv .venv               # o: python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m app.agent.embed --descargar   # modelo de embeddings a data\models (una vez)
cd ..\frontend
npm install
cd ..
```

## Ejecutar

```powershell
# Terminal 1 — backend (http://localhost:8000/docs)
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000

# Terminal 2 — interfaz (http://localhost:5173)
cd frontend
npm run dev
```

Con `AGENT_MODE=live` (valor de `.env.example`) se usa el agente. Con `AGENT_MODE=stub` se ven datos DEMO sintéticos. Al cambiar de modo, el backend regenera las fichas automáticamente.

## Pruebas y evaluación

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q          # T01–T10 + API
cd ..
backend\.venv\Scripts\python eval\run_eval.py   # agente vs baseline → eval\resultados\
```

## Datos (snapshot congelado y versionado)

El snapshot ya está en `data/raw/` con `manifest.json` (SHA-256, consultas, fecha de corte). Para regenerarlo (requiere internet; cambia los resultados):

```powershell
python data\scripts\download_snapshot.py all
python data\scripts\validate.py
```

| Archivo | Contenido |
|---|---|
| `data/raw/noticias.csv` | TVN RSS (solo título, URL, fecha) + GDELT DOC 2.0 |
| `data/raw/indicadores.csv` | Banco Mundial: 6 países × 6 indicadores × 2010–2024 |
| `data/raw/eventos.geojson` | USGS: sismos 2024, M ≥ 3, caja lat 5–12, lon −86/−76 |
| `data/synthetic/casos_controlados.csv` | Casos de prueba sintéticos rotulados (inyección, contradicciones, recirculada, agencia) |
| `data/processed/` | Noticias válidas/errores, reporte de calidad, `fichas.jsonl`, caché de embeddings |
| `eval/benchmark.jsonl` | 60 consultas (40 dev / 20 reservadas) |

Diccionario y licencias: [docs/06_DATASET.md](docs/06_DATASET.md).

## Demo sin internet (T10)

1. Desconecta la red.
2. Arranca backend e interfaz como arriba. Los embeddings salen del modelo local y de la caché.
3. Los borradores usan la caché del LLM (`data/cache/llm/`) si existe; si no, la plantilla determinista. Para forzar este modo: `LLM_OFFLINE=1` en `.env`.
4. Si falta el modelo de embeddings, el sistema avisa y usa un respaldo léxico (peor calidad), sin caerse.

## Docker (solo backend)

```powershell
docker compose up --build
```

## Estructura

```
backend/app/agent/   IA: embeddings, temas, eventos, contexto, puntaje, consultas, borradores, seguridad, baseline
backend/app/         API FastAPI, SQLite, fórmula de puntaje
backend/tests/       pruebas T01–T10
frontend/src/        interfaz del flujo completo
data/                snapshot, scripts de descarga y validación, casos sintéticos
eval/                benchmark, etiquetas, evaluación
docs/                documentación y export para Notion (docs/notion_export/)
```
