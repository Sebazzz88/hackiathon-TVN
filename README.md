# Copiloto editorial TVN — "De la señal a la decisión" (hackIAthon 2026)

## Ejecutar
```bash
cp .env.example .env
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload            # http://localhost:8000/docs
# Frontend (otra terminal)
cd frontend && npm install && npm run dev  # http://localhost:5173
# Tests
cd backend && pytest -q
# Alternativa: docker compose up --build (solo backend)
```
## Datos
`python data/scripts/download_snapshot.py all` y luego `python data/scripts/validate.py`.
Estado actual: `AGENT_MODE=stub` usa datos DEMO sintéticos. La IA se conecta en `backend/app/agent_interface.py` (ver `NOTA_PERSONA_1.md`).
