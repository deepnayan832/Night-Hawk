# NightHawk setup — portable from any clone location
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "nighthawk-backend"
$ui = Join-Path $root "nighthawk-ui"
$venv = Join-Path $root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

Write-Host "=== NIGHTHAWK SETUP ===" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ was not found. Install Python and enable 'Add Python to PATH'."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js 20+ and npm are required to build the bundled Three.js renderer. Install Node.js, then reopen PowerShell."
}
if (-not (Test-Path (Join-Path $backend "main.py"))) { throw "Backend source is missing: $backend" }
if (-not (Test-Path (Join-Path $ui "package.json"))) { throw "Three.js build project is missing: $ui" }

if (-not (Test-Path $venv)) {
    Write-Host "[1/5] Creating Python virtual environment..."
    python -m venv $venv
}
Write-Host "[2/5] Installing Python dependencies..."
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $python -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed." }

Write-Host "[3/5] Installing local Three.js build dependencies..."
Push-Location $ui
try {
    npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm dependency installation failed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Three.js frontend build failed." }
} finally { Pop-Location }

Write-Host "[4/5] Running Python unit tests..."
Push-Location $backend
try {
    & $python -m compileall -q .
    if ($LASTEXITCODE -ne 0) { throw "Python source compilation failed." }
    & $python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed. Review the output above." }
} finally { Pop-Location }

Write-Host "[5/5] Setup complete." -ForegroundColor Green
Write-Host "Run .\start.ps1 to launch NightHawk." -ForegroundColor Cyan
