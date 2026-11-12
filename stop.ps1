<#
.SYNOPSIS
Project Nighthawk - Stop Script (Windows x64)
#>

$baseDir = "C:\Users\nayan\project-nighthawk"
$pidFile = Join-Path $baseDir "nighthawk.pid"

Write-Host "Stopping Project Nighthawk..." -ForegroundColor Yellow

$stopped = $false

if (Test-Path $pidFile) {
    $procId = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($procId) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-Host "[+] Terminated process with PID: $procId" -ForegroundColor Green
            $stopped = $true
        } catch {
            Write-Host "Process $procId was not active." -ForegroundColor Gray
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

# Also ensure port 8765 is released
$portConnections = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
if ($portConnections) {
    foreach ($conn in $portConnections) {
        $pId = $conn.OwningProcess
        if ($pId -and $pId -ne 0) {
            try {
                Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue
                Write-Host "[+] Released port 8765 by stopping process $pId." -ForegroundColor Green
                $stopped = $true
            } catch {}
        }
    }
}

if ($stopped) {
    Write-Host "[+] Project Nighthawk successfully shut down." -ForegroundColor Green
} else {
    Write-Host "Project Nighthawk is not running." -ForegroundColor Gray
}
