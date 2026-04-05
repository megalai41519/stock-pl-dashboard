"""
Stock P&L Dashboard — FastAPI entry point.
Run: uvicorn main:app --reload  (dev)
     python main.py              (packaged / production)
"""

import sys
import os
import threading
import webbrowser
import time
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# ── resolve paths before any local imports ──────────────────────────────────
from app.config import get_base_path, FRONTEND_DIR

# ── load .env from same folder as the executable / main.py ─────────────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(get_base_path(), ".env"))

# ── routers ─────────────────────────────────────────────────────────────────
from app.routes.portfolio import router as portfolio_router
from app.routes.charts import router as charts_router
from app.routes.news import router as news_router
from app.data.cache import init_cache

init_cache()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="Stock P&L Dashboard",
    description="Personal portfolio analytics dashboard",
    version="1.0.0",
)

# ── API routes ───────────────────────────────────────────────────────────────
app.include_router(portfolio_router, prefix="/api")
app.include_router(charts_router,   prefix="/api")
app.include_router(news_router,     prefix="/api")

# ── serve the single-page frontend ──────────────────────────────────────────
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── auto-open browser when running as packaged app ───────────────────────────
def _open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    log.info("Starting Stock P&L Dashboard on http://localhost:8000")
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(
        app,                       # object, NOT string — required for PyInstaller
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
