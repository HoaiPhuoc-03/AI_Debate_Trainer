$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    python -m venv .venv
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r backend\requirements.txt -r requirements-desktop.txt

& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name "AI Debate Trainer" `
    --add-data "frontend;frontend" `
    --add-data "backend;backend" `
    desktop_app.py

Write-Host ""
Write-Host "Build complete: dist\AI Debate Trainer\AI Debate Trainer.exe"
