# NightHawk environment diagnostics
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$backend = Join-Path $root "nighthawk-backend"
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
Write-Host "=== NIGHTHAWK DIAGNOSTICS ===" -ForegroundColor Cyan
if ($pythonCmd) { python --version } else { Write-Host "Python not found in PATH" -ForegroundColor Red }
$python = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $python) {
    & $python -c "import fastapi, uvicorn; print('FastAPI and Uvicorn imports: OK')"
    if ($LASTEXITCODE -ne 0) { Write-Host "Python dependencies missing. Run .\setup.ps1" -ForegroundColor Red }
} else { Write-Host "Virtual environment missing. Run .\setup.ps1" -ForegroundColor Yellow }
if (Test-Path (Join-Path $backend "main.py")) { Write-Host "Backend source: present" -ForegroundColor Green } else { Write-Host "Backend source: missing" -ForegroundColor Red }
if (Test-Path (Join-Path $backend "static\index.html")) { Write-Host "Frontend: present" -ForegroundColor Green } else { Write-Host "Frontend: missing" -ForegroundColor Red }
if (Get-Command netsh -ErrorAction SilentlyContinue) {
    netsh wlan show interfaces
} else { Write-Host "Windows netsh not available (live Wi-Fi scan requires Windows)." -ForegroundColor Yellow }
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/health" -TimeoutSec 2
    Write-Host "Local API: ONLINE · $($health.version)" -ForegroundColor Green
} catch { Write-Host "Local API: not running" -ForegroundColor Gray }
