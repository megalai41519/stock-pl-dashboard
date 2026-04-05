# build/build_windows.ps1 — Build StockDashboard.exe
# Run from project root: .\build\build_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "──────────────────────────────────────────"
Write-Host " Stock P&L Dashboard — Windows Build"
Write-Host "──────────────────────────────────────────"

# Create venv if absent
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment…"
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies…"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

Write-Host "Running PyInstaller…"
pyinstaller build\stock_dashboard_win.spec `
    --distpath dist\windows `
    --workpath "$env:TEMP\pyinstaller_work" `
    --noconfirm

Write-Host ""
Write-Host "✔  Build complete!"
Write-Host "   Output: dist\windows\StockDashboard.exe"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Place portfolio.csv and .env next to StockDashboard.exe"
Write-Host "  2. Double-click to run — browser opens automatically"
Write-Host "  3. Windows SmartScreen: click More info → Run anyway"
