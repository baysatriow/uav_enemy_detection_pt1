#requires -Version 7.0
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ProjectRoot
try {
    if (-not (Get-Command py.exe -ErrorAction SilentlyContinue)) {
        throw "Python Launcher py.exe tidak ditemukan. Pasang Python 3.11 terlebih dahulu."
    }

    py -3.11 -m venv .venv-training
    if ($LASTEXITCODE -ne 0) { throw "Gagal membuat .venv-training dengan Python 3.11." }

    $PythonExe = Join-Path $ProjectRoot ".venv-trainingScriptspython.exe"
    & $PythonExe -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Gagal memperbarui pip." }

    & $PythonExe -m pip install -r (Join-Path $ProjectRoot "requirements-training.txt")
    if ($LASTEXITCODE -ne 0) { throw "Gagal memasang requirements training." }

    & $PythonExe -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Ditemukan dependency yang tidak konsisten." }

    & $PythonExe -m ipykernel install --user --name uav-yolo26-training --display-name "UAV YOLO26 Training GPU"
    if ($LASTEXITCODE -ne 0) { throw "Gagal mendaftarkan kernel Jupyter." }

    Write-Host "Selesai. Pilih kernel: UAV YOLO26 Training GPU"
}
finally {
    Pop-Location
}
