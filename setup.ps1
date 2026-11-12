# NightHawk setup — portable from any clone location
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "nighthawk-backend"
$venv = Join-Path $root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

Write-Host "=== NIGHTHAWK SETUP ===" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ was not found. Install Python and enable 'Add Python to PATH'."
}
if (-not (Test-Path (Join-Path $backend "main.py"))) {
    throw "Backend source is missing: $backend"
}
if (-not (Test-Path $venv)) {
    Write-Host "[1/4] Creating local virtual environment..."
    python -m venv $venv
}
Write-Host "[2/4] Installing Python dependencies..."
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $python -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

Write-Host "[3/4] Running RF core tests..."
Push-Location $backend
try {
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed. Review the output above." }
} finally { Pop-Location }

Write-Host "[4/4] Setup complete." -ForegroundColor Green
Write-Host "Run .\start.ps1 to launch NightHawk." -ForegroundColor Cyan
