# Demo en un contenedor: interfaz compilada + backend en http://localhost:8000. Sin credenciales; sin red por defecto.
# docker compose up --build      (NO probado en el equipo de desarrollo: no tiene Docker. Ruta principal: run_demo.ps1)
FROM node:20-alpine AS interfaz
WORKDIR /f
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY data /app/data
COPY eval /app/eval
COPY --from=interfaz /f/dist /app/frontend/dist
ENV AGENT_MODE=live LLM_OFFLINE=1 DATA_DIR=/app/data DB_PATH=/app/data/app.db
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
