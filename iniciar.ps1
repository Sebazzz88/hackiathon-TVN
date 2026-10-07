# Copiloto TVN: instala, enciende y apaga todo en Windows (backend, interfaz e IA local Hermes 3 vía Ollama).
# Uso, desde la carpeta del repo:
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar   # la primera vez: instala todo y enciende
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1             # las siguientes veces: enciende
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Apagar     # apaga backend e interfaz
param([switch]$Instalar, [switch]$Apagar)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$py = Join-Path $raiz "backend\.venv\Scripts\python.exe"
$modelo = "hermes3:3b"

function Paso($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor Cyan }

function Apagar-App {
    # Solo lo de ESTE repo: las ventanas que abre este script (con todo su árbol de procesos), el servidor uvicorn
    # de la app y el Vite de esta carpeta. No toca otros procesos de Python o Node del equipo.
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq "powershell.exe" -and $_.CommandLine -and $_.CommandLine -match "uvicorn app.main:app|npm run dev" -and
        $_.CommandLine -like "*$raiz*"
    } | ForEach-Object { taskkill /T /F /PID $_.ProcessId 2>$null | Out-Null }
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and (
            ($_.Name -eq "python.exe" -and $_.CommandLine -match "uvicorn app\.main:app --port 8000") -or
            ($_.Name -eq "node.exe" -and $_.CommandLine -match "vite" -and $_.CommandLine -like "*$raiz*"))
    } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if ($Apagar) {
    Apagar-App
    Write-Host "Backend e interfaz apagados. (Ollama sigue corriendo en segundo plano; se puede cerrar desde la bandeja de Windows.)"
    exit 0
}

# ---------------------------------------------------------------- configuración
if (-not (Test-Path (Join-Path $raiz ".env"))) {
    Copy-Item (Join-Path $raiz ".env.example") (Join-Path $raiz ".env")
    Write-Host "Creado .env a partir de .env.example (IA local Hermes 3, sin claves)."
}

# ---------------------------------------------------------------- backend (Python)
if ($Instalar -or -not (Test-Path $py)) {
    Paso "Instalando backend (Python)"
    Push-Location (Join-Path $raiz "backend")
    if (-not (Test-Path $py)) {
        if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv } else { python -m venv .venv }
    }
    & $py -m pip install --upgrade pip | Out-Null
    & $py -m pip install -r requirements.txt
    Pop-Location
}
if (-not (Test-Path (Join-Path $raiz "data\models"))) {
    Paso "Descargando modelo de embeddings (una vez, ~0,22 GB)"
    Push-Location (Join-Path $raiz "backend"); & $py -m app.agent.embed --descargar; Pop-Location
}

# ---------------------------------------------------------------- interfaz (Node)
if ($Instalar -or -not (Test-Path (Join-Path $raiz "frontend\node_modules"))) {
    Paso "Instalando interfaz (Node)"
    Push-Location (Join-Path $raiz "frontend"); npm install --no-audit --no-fund; Pop-Location
}

# ---------------------------------------------------------------- IA generativa local: Ollama + Hermes 3
Paso "IA generativa local (Ollama + $modelo)"
$ollama = (Get-Command ollama -ErrorAction SilentlyContinue).Source
if (-not $ollama) { $c = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"; if (Test-Path $c) { $ollama = $c } }
if (-not $ollama -and $Instalar) {
    Write-Host "Instalando Ollama con winget..."
    winget install --id Ollama.Ollama -e --silent --accept-package-agreements --accept-source-agreements
    $c = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"; if (Test-Path $c) { $ollama = $c }
}
if ($ollama) {
    $vivo = $false
    try { Invoke-RestMethod http://localhost:11434/api/version -TimeoutSec 3 | Out-Null; $vivo = $true } catch {}
    if (-not $vivo) {
        Start-Process $ollama -ArgumentList "serve" -WindowStyle Hidden
        for ($i = 0; $i -lt 15 -and -not $vivo; $i++) {
            Start-Sleep 1
            try { Invoke-RestMethod http://localhost:11434/api/version -TimeoutSec 2 | Out-Null; $vivo = $true } catch {}
        }
    }
    $lista = & $ollama list 2>$null | Out-String
    if ($lista -notmatch [regex]::Escape($modelo)) {
        Write-Host "Descargando $modelo (una vez, ~2 GB)..."
        & $ollama pull $modelo
    }
    Write-Host "Ollama listo con $modelo (local, gratuito, sin internet)."
} else {
    Write-Host "Ollama no está instalado: la app funciona igual, pero sin IA generativa (usa caché o plantilla)." -ForegroundColor Yellow
    Write-Host "Para activarla: powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar" -ForegroundColor Yellow
}

# ---------------------------------------------------------------- encender
Apagar-App  # evita dos copias si ya estaba encendida
Paso "Encendiendo backend en http://localhost:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Copiloto TVN - backend'; cd '$raiz\backend'; & '$py' -m uvicorn app.main:app --port 8000"
Paso "Encendiendo interfaz en http://localhost:5173"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='Copiloto TVN - interfaz'; cd '$raiz\frontend'; npm run dev"

$ok = $false
for ($i = 0; $i -lt 40 -and -not $ok; $i++) {
    Start-Sleep 1
    try { Invoke-RestMethod http://localhost:8000/health -TimeoutSec 2 | Out-Null; $ok = $true } catch {}
}
if ($ok) {
    $ia = (Invoke-RestMethod http://localhost:8000/api/meta).ia
    $txt = if ($ia.conectado) { "IA generativa conectada: $($ia.modelo)" } else { "IA generativa no disponible: $($ia.motivo)" }
    Write-Host "Backend listo. $txt" -ForegroundColor Green
} else {
    Write-Host "El backend tarda en responder; revisa la ventana 'Copiloto TVN - backend'." -ForegroundColor Yellow
}
Start-Sleep 3
Start-Process "http://localhost:5173"
Write-Host ""
Write-Host "Listo: http://localhost:5173  ·  Para apagar: powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Apagar"
