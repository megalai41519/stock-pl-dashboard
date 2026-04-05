"""
app/config.py — centralised paths, constants, and settings.
Works correctly whether running:
  • python main.py  (development)
  • ./StockDashboard.app  (Mac PyInstaller bundle)
  • StockDashboard.exe    (Windows PyInstaller bundle)
"""

import os
import sys


def get_base_path() -> str:
    """
    Return the folder that contains portfolio.csv and .env.

    PyInstaller Mac .app layout:
        StockDashboard.app/
          Contents/
            MacOS/          ← sys.executable lives here
            Resources/
        portfolio.csv       ← we want THIS folder (3 levels up from MacOS/)

    PyInstaller Windows .exe layout:
        StockDashboard.exe  ← one level up from _MEIPASS
        portfolio.csv       ← same folder as .exe

    Development:
        main.py lives in project root → same folder as portfolio.csv
    """
    if getattr(sys, "frozen", False):
        exe_path = sys.executable  # e.g. .../StockDashboard.app/Contents/MacOS/StockDashboard

        if sys.platform == "darwin":
            # Walk up: MacOS → Contents → StockDashboard.app → folder beside .app
            macos_dir   = os.path.dirname(exe_path)        # .../MacOS
            contents_dir = os.path.dirname(macos_dir)      # .../Contents
            app_bundle   = os.path.dirname(contents_dir)   # .../StockDashboard.app
            return os.path.dirname(app_bundle)             # folder containing .app
        else:
            # Windows: .exe is in a flat folder
            return os.path.dirname(exe_path)
    else:
        # Running as plain Python — main.py is at project root
        return os.path.dirname(os.path.abspath(sys.argv[0]))


def get_resource_path(relative_path: str) -> str:
    """
    Locate a bundled resource (frontend/, etc.) inside a PyInstaller bundle,
    or relative to the project root in development.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


# ── derived paths ─────────────────────────────────────────────────────────────
BASE_PATH    = get_base_path()
PORTFOLIO_CSV = os.path.join(BASE_PATH, "portfolio.csv")
CACHE_DB      = os.path.join(BASE_PATH, "cache.db")
FRONTEND_DIR  = get_resource_path("frontend")

# ── API settings ──────────────────────────────────────────────────────────────
FMP_BASE_URL  = "https://financialmodelingprep.com/api/v3"
CACHE_TTL_SEC = 15 * 60   # 15 minutes

# ── retry / backoff ───────────────────────────────────────────────────────────
RETRY_ATTEMPTS = 3
RETRY_DELAYS   = [2, 4, 8]   # seconds between attempts

# ── yfinance browser-spoof headers ────────────────────────────────────────────
YFINANCE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
