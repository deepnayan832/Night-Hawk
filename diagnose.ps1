# NightHawk environment diagnostics
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$backend = Join-Path $root "nighthawk-backend"
Write-Host "=== NIGHTHAWK DIAGNOSTICS ===" -ForegroundColor Cyan

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) { python --version } else { Write-Host "Python not found in PATH" -ForegroundColor Red }
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) { node --version } else { Write-Host "Node.js not found; required to build Three.js." -ForegroundColor Red }
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) { npm --version } else { Write-Host "npm not found; required to build Three.js." -ForegroundColor Red }

$venvCandidates = @(
    (Join-Path $root ".venv\Scripts\python.exe"),
    (Join-Path $root "venv\Scripts\python.exe")
)
$python = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) { $python = Join-Path $root ".venv\Scripts\python.exe" }
if (Test-Path $python) {
    & $python -c "import fastapi, uvicorn, serial; print('FastAPI, Uvicorn and pyserial imports: OK')"
    if ($LASTEXITCODE -ne 0) { Write-Host "Python dependencies missing. Run .\setup.ps1" -ForegroundColor Red }
} else { Write-Host "Virtual environment missing. Run .\setup.ps1" -ForegroundColor Yellow }

foreach ($path in @("main.py","wifi.py","network_intel.py","rf.py","db.py","csi.py","volumetric.py","scanplan.py")) {
    if (Test-Path (Join-Path $backend $path)) { Write-Host "$path : present" -ForegroundColor Green }
    else { Write-Host "$path : missing" -ForegroundColor Red }
}
if (Test-Path (Join-Path $backend "static\index.html")) { Write-Host "Frontend HTML: present" -ForegroundColor Green }
if (Test-Path (Join-Path $backend "static\three-scene.js")) { Write-Host "Bundled Three.js renderer: present" -ForegroundColor Green }
else { Write-Host "Three.js bundle missing. Run .\setup.ps1" -ForegroundColor Yellow }

if (Get-Command netsh -ErrorAction SilentlyContinue) {
    netsh wlan show interfaces
} else { Write-Host "Windows netsh not available (live Wi-Fi scan requires Windows)." -ForegroundColor Yellow }

try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/health" -TimeoutSec 2
    Write-Host "Local API: ONLINE · $($health.version)" -ForegroundColor Green
} catch { Write-Host "Local API: not running" -ForegroundColor Gray }
