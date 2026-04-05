#!/usr/bin/env bash
# build/build_mac.sh — Build StockDashboard.app
# Run from project root: bash build/build_mac.sh

set -euo pipefail

echo "──────────────────────────────────────────"
echo " Stock P&L Dashboard — Mac Build"
echo "──────────────────────────────────────────"

# Ensure venv exists
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment…"
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies…"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

echo "Running PyInstaller…"
pyinstaller build/stock_dashboard_mac.spec \
  --distpath dist/mac \
  --workpath /tmp/pyinstaller_work \
  --noconfirm

echo ""
echo "✔  Build complete!"
echo "   Output: dist/mac/StockDashboard.app"
echo ""
echo "Next steps:"
echo "  1. Move StockDashboard.app out of Downloads before running"
echo "  2. Place portfolio.csv and .env next to StockDashboard.app"
echo "  3. First run: right-click → Open (bypasses Gatekeeper)"
echo "  4. If quarantine error: xattr -cr StockDashboard.app"
