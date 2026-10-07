# Nexo · Copiloto editorial para TVN: demo en UN comando, UNA ventana y UN puerto (http://localhost:8000). Sin login ni credenciales.
# Requisito: haber instalado una vez con  powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar
# Uso, desde la carpeta del repo:
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1            # con Hermes 3 local si Ollama está encendido
#   powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Offline   # 100 % sin red: caché de la IA o plantilla
# Se apaga con Ctrl+C en esta misma ventana. No abre otras ventanas.
param([switch]$Offline, [switch]$SinNavegador, [int]$Puerto = 8000)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
$py = Join-Path $raiz "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Falta instalar el backend. Ejecuta una vez: powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Instalar" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path (Join-Path $raiz ".env"))) { Copy-Item (Join-Path $raiz ".env.example") (Join-Path $raiz ".env") }

# Interfaz compilada: se recompila solo si falta o si el código cambió después de la última compilación.
$dist = Join-Path $raiz "frontend\dist\index.html"
$src = Get-ChildItem (Join-Path $raiz "frontend\src") -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not (Test-Path $dist) -or ($src -and $src.LastWriteTime -gt (Get-Item $dist).LastWriteTime)) {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "Compilando la interfaz…" -ForegroundColor Cyan
        Push-Location (Join-Path $raiz "frontend"); npm run build --silent; Pop-Location
    } elseif (-not (Test-Path $dist)) {
        Write-Host "Falta la interfaz compilada y Node.js no está instalado. Ejecuta iniciar.ps1 -Instalar." -ForegroundColor Yellow
        exit 1
    }
}

$env:AGENT_MODE = "live"
if ($Offline) { $env:LLM_OFFLINE = "1"; Write-Host "Modo sin red: la IA generativa usa solo su caché; si no hay, plantilla o abstención." -ForegroundColor Cyan }

if (-not $SinNavegador) {
    # Abre el navegador cuando el backend responda (en segundo plano, sin ventana).
    Start-Job -ArgumentList $Puerto -ScriptBlock {
        param($p)
        for ($i = 0; $i -lt 90; $i++) {
            Start-Sleep 1
            try { Invoke-RestMethod "http://localhost:$p/health" -TimeoutSec 2 | Out-Null; Start-Process "http://localhost:$p"; return } catch {}
        }
    } | Out-Null
}
Write-Host "Nexo · Copiloto editorial en http://localhost:$Puerto  ·  Ctrl+C para apagar" -ForegroundColor Green
Push-Location (Join-Path $raiz "backend")
try { & $py -m uvicorn app.main:app --host 127.0.0.1 --port $Puerto } finally { Pop-Location; Get-Job | Remove-Job -Force }
