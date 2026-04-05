"""
app/routes/portfolio.py

GET /api/portfolio  → full portfolio with KPIs and holdings table data.
"""

import logging
import platform
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.data.loader import load_portfolio, PortfolioLoadError, detect_csv_issues
from app.data.fetcher import fetch_quote, get_warnings, clear_warnings
from app.data import cache as cache_store
from app.analytics.pnl import calc_holding, calc_portfolio

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/portfolio")
async def get_portfolio():
    """
    Returns:
        {
          "kpis": {...},
          "holdings": [...],
          "errors": [...],    # non-fatal per-ticker errors
          "warnings": {...},  # system-level warnings for the UI banner
        }
    """
    # ── load CSV ─────────────────────────────────────────────────────────────
    try:
        raw_holdings = load_portfolio()
    except PortfolioLoadError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # ── check portfolio-level cache ──────────────────────────────────────────
    cache_key = "portfolio:full"
    cached = cache_store.get(cache_key)
    if cached:
        log.info("Serving portfolio from cache.")
        # Still inject live warnings even from cache
        cached["warnings"] = _build_warnings()
        return JSONResponse(cached)

    # ── fetch quotes and enrich ──────────────────────────────────────────────
    enriched = []
    errors   = []

    for row in raw_holdings:
        ticker   = row["ticker"]
        shares   = row["shares"]
        avg_cost = row["avg_cost"]

        quote = fetch_quote(ticker)

        if quote.get("error"):
            errors.append({"ticker": ticker, "message": quote["error"]})

        holding = calc_holding(ticker, shares, avg_cost, quote)
        enriched.append(holding)

    # ── portfolio-level calcs ────────────────────────────────────────────────
    result = calc_portfolio(enriched)
    result["errors"]   = errors
    result["warnings"] = _build_warnings()

    cache_store.set(cache_key, result)
    return JSONResponse(result)


@router.post("/portfolio/refresh")
async def refresh_portfolio():
    """Force-bust the portfolio cache and all quote caches."""
    cache_store.purge_expired()
    cache_store.invalidate("portfolio:full")
    clear_warnings()
    return {"status": "cache cleared"}


def _build_warnings() -> dict:
    """Collect all system-level warnings to surface in the UI."""
    w = get_warnings()
    csv_issues = detect_csv_issues()
    return {
        "fmp_rate_limited":     w.get("fmp_rate_limited", False),
        "yfinance_fallback":    w.get("yfinance_fallback", False),
        "csv_numbers_format":   csv_issues.get("numbers_format", False),
        "mac_translocation_risk": _is_mac_translocation_risk(),
    }


def _is_mac_translocation_risk() -> bool:
    """
    Warn if running on macOS and the executable path contains /AppTranslocation/
    or is still inside the Downloads folder.
    """
    if platform.system() != "Darwin":
        return False
    import sys, os
    exe = sys.executable.lower()
    return "/apptranslocation/" in exe or "/downloads/" in exe
