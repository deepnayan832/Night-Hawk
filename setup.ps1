<#
.SYNOPSIS
Project Nighthawk - Complete Automated Setup Script
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   PROJECT NIGHTHAWK — AUTOMATED WINDOWS SETUP           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$baseDir = "C:\Users\nayan\project-nighthawk"
$venvDir = Join-Path $baseDir "venv"
$pipExe = Join-Path $venvDir "Scripts\pip.exe"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$uiDir = Join-Path $baseDir "nighthawk-ui"

# Step 1: Python Virtual Environment
Write-Host "[1/4] Configuring Python Virtual Environment..." -ForegroundColor Yellow
if (-not (Test-Path $venvDir)) {
    Write-Host "  Creating venv at $venvDir..." -ForegroundColor Gray
    python -m venv $venvDir
}

Write-Host "  Installing backend dependencies via pip..." -ForegroundColor Gray
& $pipExe install --quiet --upgrade pip
& $pipExe install --quiet fastapi uvicorn pydantic numpy scipy pyserial websockets httpx
Write-Host "  [+] Backend Virtual Environment Ready." -ForegroundColor Green

# Step 2: Frontend Dependencies
Write-Host ""
Write-Host "[2/4] Installing Frontend NPM Dependencies..." -ForegroundColor Yellow
Push-Location $uiDir
try {
    npm install --silent
    Write-Host "  [+] Node modules installed successfully." -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 3: Frontend Production Build
Write-Host ""
Write-Host "[3/4] Building Three.js & React WebGL Application..." -ForegroundColor Yellow
Push-Location $uiDir
try {
    npm run build
    Write-Host "  [+] Production WebGL bundle compiled into nighthawk-ui/dist/." -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 4: Verification Unit Tests
Write-Host ""
Write-Host "[4/4] Executing Backend Integration & Unit Tests..." -ForegroundColor Yellow
$testScript = Join-Path $baseDir "nighthawk-backend\test_backend.py"
& $pythonExe $testScript
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [+] All Backend Unit Tests Passed." -ForegroundColor Green
} else {
    Write-Host "  [-] Some tests failed. Please inspect test_backend.py output." -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SETUP COMPLETE! Run .\start.ps1 to launch application. " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
