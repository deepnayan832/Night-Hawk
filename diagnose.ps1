<#
.SYNOPSIS
Project Nighthawk - System Diagnostics & Hardware Verification Script
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   PROJECT NIGHTHAWK — 3D WI-FI SYSTEM DIAGNOSTICS        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# 1. Environment checks
Write-Host "[1/5] Checking System Prerequisites..." -ForegroundColor Yellow
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $pyVer = & python --version 2>&1
    Write-Host "  [+] Python Detected: $pyVer" -ForegroundColor Green
} else {
    Write-Host "  [-] Python NOT found in PATH!" -ForegroundColor Red
    $allPassed = $false
}

$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    $nodeVer = & node --version 2>&1
    Write-Host "  [+] Node.js Detected: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  [-] Node.js NOT found in PATH!" -ForegroundColor Red
    $allPassed = $false
}

# 2. Virtual environment check
Write-Host ""
Write-Host "[2/5] Checking Python Virtual Environment..." -ForegroundColor Yellow
$venvPython = "C:\Users\nayan\project-nighthawk\venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "  [+] Virtual Environment present: $venvPython" -ForegroundColor Green
    $pkgCheck = & $venvPython -c "
import fastapi, uvicorn, pydantic, numpy, scipy, serial, websockets
print('All core dependencies imported successfully.')
" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [+] Backend Dependencies: OK ($pkgCheck)" -ForegroundColor Green
    } else {
        Write-Host "  [-] Missing dependencies in venv: $pkgCheck" -ForegroundColor Red
        $allPassed = $false
    }
} else {
    Write-Host "  [-] Virtual environment missing at $venvPython. Run setup.ps1 first." -ForegroundColor Red
    $allPassed = $false
}

# 3. Windows Native Wi-Fi Hardware Diagnostics
Write-Host ""
Write-Host "[3/5] Querying Windows WLAN AutoConfig (Tier 1 Hardware)..." -ForegroundColor Yellow
$wlanLines = netsh wlan show interfaces 2>&1
$wlanText = $wlanLines -join "`n"

if ($wlanText -match "Name\s*:\s*(.+)") {
    Write-Host "  [+] Wi-Fi Interface Found: $($Matches[1].Trim())" -ForegroundColor Green

    if ($wlanText -match "Description\s*:\s*(.+)") {
        Write-Host "      Adapter: $($Matches[1].Trim())" -ForegroundColor Gray
    }
    if ($wlanText -match "State\s*:\s*(.+)") {
        $state = $Matches[1].Trim()
        $color = if ($state -eq "connected") { "Green" } else { "Yellow" }
        Write-Host "      State: $state" -ForegroundColor $color
    }
    if ($wlanText -match "SSID\s*:\s*(.+)") {
        Write-Host "      Connected SSID: $($Matches[1].Trim())" -ForegroundColor Cyan
    }
    if ($wlanText -match "AP BSSID\s*:\s*(.+)") {
        Write-Host "      AP BSSID: $($Matches[1].Trim())" -ForegroundColor Gray
    }
    if ($wlanText -match "Signal\s*:\s*(.+)") {
        Write-Host "      Signal Quality: $($Matches[1].Trim())" -ForegroundColor Green
    }
    if ($wlanText -match "Rssi\s*:\s*(.+)") {
        Write-Host "      True RSSI: $($Matches[1].Trim()) dBm" -ForegroundColor Green
    }
} else {
    Write-Host "  [-] No active Wi-Fi interface detected via netsh!" -ForegroundColor Red
    $allPassed = $false
}

# 4. Optional Hardware Scan (CSI ESP32 COM Ports)
Write-Host ""
Write-Host "[4/5] Scanning Optional External Hardware Modules (Tier 2 & 3)..." -ForegroundColor Yellow
if (Test-Path $venvPython) {
    $comPorts = & $venvPython -c "
import serial.tools.list_ports
ports = [p.device + ' (' + p.description + ')' for p in serial.tools.list_ports.comports()]
print(','.join(ports) if ports else 'NONE')
" 2>&1
    if ($comPorts -ne "NONE" -and $comPorts.Trim()) {
        Write-Host "  [+] USB COM Ports Detected (ESP32 Candidate): $comPorts" -ForegroundColor Green
    } else {
        Write-Host "  [i] No USB Virtual COM ports detected. CSI module will run in high-fidelity Simulation Mode." -ForegroundColor Cyan
    }
}

# 5. Production UI Build Verification
Write-Host ""
Write-Host "[5/5] Checking Compiled WebGL / React Production Bundle..." -ForegroundColor Yellow
$distIndex = "C:\Users\nayan\project-nighthawk\nighthawk-ui\dist\index.html"
if (Test-Path $distIndex) {
    $size = (Get-Item $distIndex).Length
    Write-Host "  [+] UI Production Build present ($distIndex)" -ForegroundColor Green
} else {
    Write-Host "  [-] UI Production Build not found. Run setup.ps1 to build." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  DIAGNOSTICS PASSED: System is ready for Project Nighthawk! " -ForegroundColor Green
    Write-Host "  Run .\start.ps1 to launch application." -ForegroundColor Green
} else {
    Write-Host "  DIAGNOSTICS WARNINGS DETECTED. Please review the items above." -ForegroundColor Yellow
}
Write-Host "==========================================================" -ForegroundColor Cyan
