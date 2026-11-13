$baseDir = "C:\Users\nayan\project-nighthawk"
$venvDir = Join-Path $baseDir "venv"
if (-not (Test-Path $venvDir)) {
    Write-Output "Creating virtual environment at $venvDir..."
    python -m venv $venvDir
}

$pip = Join-Path $venvDir "Scripts\pip.exe"
Write-Output "Installing backend dependencies using $pip..."
& $pip install fastapi uvicorn pydantic numpy scipy pyserial websockets
Write-Output "VENV_SETUP_COMPLETE"
