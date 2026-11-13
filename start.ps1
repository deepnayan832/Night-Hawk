# Start NightHawk on localhost only
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "nighthawk-backend"
$venvCandidates = @(
    (Join-Path $root ".venv\Scripts\python.exe"),
    (Join-Path $root "venv\Scripts\python.exe")
)
$python = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) { $python = Join-Path $root ".venv\Scripts\python.exe" }
$sceneBundle = Join-Path $backend "static\three-scene.js"
$pidFile = Join-Path $root ".nighthawk-server.pid"
$url = "http://127.0.0.1:8765"

if (-not (Test-Path $python)) { throw "Virtual environment not found. Run .\setup.ps1 first." }
if (-not (Test-Path (Join-Path $backend "main.py"))) { throw "Backend source not found." }
if (-not (Test-Path $sceneBundle)) { throw "Three.js bundle missing. Run .\setup.ps1 to build the 3D renderer." }

try {
    $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2
    if ($health.ok) {
        Write-Host "NightHawk is already running at $url" -ForegroundColor Green
        Start-Process $url
        exit 0
    }
} catch {}

Write-Host "Starting NightHawk at $url ..." -ForegroundColor Cyan
$proc = Start-Process -FilePath $python -ArgumentList @(
    "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8765"
) -WorkingDirectory $backend -PassThru -WindowStyle Hidden
$proc.Id | Set-Content -Path $pidFile -Encoding ascii

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2
        if ($health.ok) { $ready = $true; break }
    } catch {}
}
if (-not $ready) {
    throw "NightHawk did not become ready. Check whether port 8765 is occupied and inspect the process."
}
Write-Host "NightHawk is ready. Opening browser..." -ForegroundColor Green
Start-Process $url
Write-Host "Stop the server with .\stop.ps1" -ForegroundColor Gray
