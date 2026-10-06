# Enciende el Copiloto TVN (backend + interfaz) en Windows.
# Uso (desde la raíz del repo):
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1            # enciende
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar  # instala todo la primera vez y enciende
param([switch]$Instalar)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$py = Join-Path $raiz "backend\.venv\Scripts\python.exe"

if (-not (Test-Path (Join-Path $raiz ".env"))) {
    Copy-Item (Join-Path $raiz ".env.example") (Join-Path $raiz ".env")
    Write-Host "Creado .env a partir de .env.example (modo live, sin clave LLM)."
}

if ($Instalar -or -not (Test-Path $py)) {
    Write-Host "== Instalando backend (Python) =="
    Push-Location (Join-Path $raiz "backend")
    if (-not (Test-Path $py)) {
        if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv } else { python -m venv .venv }
    }
    & $py -m pip install --upgrade pip | Out-Null
    & $py -m pip install -r requirements.txt
    Write-Host "== Descargando modelo de embeddings (una vez, ~0,22 GB) =="
    & $py -m app.agent.embed --descargar
    Pop-Location
}

if ($Instalar -or -not (Test-Path (Join-Path $raiz "frontend\node_modules"))) {
    Write-Host "== Instalando interfaz (Node) =="
    Push-Location (Join-Path $raiz "frontend")
    npm install --no-audit --no-fund
    Pop-Location
}

Write-Host "== Encendiendo backend en http://localhost:8000 =="
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$raiz\backend'; & '$py' -m uvicorn app.main:app --port 8000"

Write-Host "== Encendiendo interfaz en http://localhost:5173 =="
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$raiz\frontend'; npm run dev"

Start-Sleep -Seconds 8
Start-Process "http://localhost:5173"
Write-Host "Listo. Para apagar, cierra las dos ventanas de PowerShell que se abrieron."
