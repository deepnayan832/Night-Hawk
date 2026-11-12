# Stop only the NightHawk process created by start.ps1
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$pidFile = Join-Path $root ".nighthawk-server.pid"
if (-not (Test-Path $pidFile)) {
    Write-Host "No NightHawk PID file found. The app may already be stopped." -ForegroundColor Gray
    exit 0
}
$rawPid = (Get-Content $pidFile -Raw).Trim()
$processId = 0
if (-not [int]::TryParse($rawPid, [ref]$processId)) {
    Remove-Item $pidFile -Force
    throw "Invalid PID file. Removed it; no process was stopped."
}
try {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction Stop
    if ($null -eq $proc) {
        Write-Host "NightHawk process is already stopped." -ForegroundColor Gray
    } elseif ($proc.CommandLine -match "uvicorn.*main:app" -and $proc.CommandLine -match "8765") {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "NightHawk stopped (PID $processId)." -ForegroundColor Green
    } else {
        Write-Warning "PID $processId no longer points to the expected NightHawk server. It was not terminated."
    }
} finally {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}
