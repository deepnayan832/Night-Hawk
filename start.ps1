<#
.SYNOPSIS
Project Nighthawk - Start Script (Windows x64)
#>

$baseDir = "C:\Users\nayan\project-nighthawk"
$backendDir = Join-Path $baseDir "nighthawk-backend"
$pythonExe = Join-Path $baseDir "venv\Scripts\python.exe"
$pidFile = Join-Path $baseDir "nighthawk.pid"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   LAUNCHING PROJECT NIGHTHAWK (3D WI-FI HOME INTEL)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Check if port 8765 is already responding
$alreadyActive = $false
try {
    $req = Invoke-WebRequest -Uri "http://127.0.0.1:8765/api/hardware/status" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($req -and $req.StatusCode -eq 200) {
        $alreadyActive = $true
    }
} catch {}

if ($alreadyActive) {
    Write-Host "[+] Project Nighthawk is already active and listening on port 8765." -ForegroundColor Green
    Write-Host "[+] Opening WebGL Application in default browser..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:8765"
    exit 0
}

Write-Host "Starting Nighthawk Python Server on http://127.0.0.1:8765 ..." -ForegroundColor Yellow

$proc = Start-Process -FilePath $pythonExe `
    -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8765 --app-dir `"$backendDir`"" `
    -WorkingDirectory $backendDir `
    -PassThru -WindowStyle Hidden

if ($proc) {
    $proc.Id | Out-File -FilePath $pidFile -Encoding ascii
    Write-Host "[+] Server process launched (PID: $($proc.Id))." -ForegroundColor Green

    # Wait up to 5 seconds for port to open
    $ready = $false
    for ($i = 0; $i -lt 10; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $testReq = Invoke-WebRequest -Uri "http://127.0.0.1:8765/api/hardware/status" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($testReq -and $testReq.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {}
    }

    if ($ready) {
        Write-Host "[+] Server is live at http://127.0.0.1:8765!" -ForegroundColor Green
        Write-Host "[+] Opening default browser..." -ForegroundColor Cyan
        Start-Process "http://127.0.0.1:8765"
    } else {
        Write-Host "[!] Server started, opening browser..." -ForegroundColor Yellow
        Start-Process "http://127.0.0.1:8765"
    }

    Write-Host ""
    Write-Host "Application is active at: http://127.0.0.1:8765" -ForegroundColor Cyan
    Write-Host "To stop the application, run: .\stop.ps1" -ForegroundColor Gray
} else {
    Write-Host "[-] Failed to start process." -ForegroundColor Red
}
