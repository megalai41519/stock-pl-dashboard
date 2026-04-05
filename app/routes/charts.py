"""
app/routes/charts.py

GET /api/chart/{ticker}?period=1M  → OHLCV candles for Plotly candlestick.
"""

import logging
from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from app.data.fetcher import fetch_history

log = logging.getLogger(__name__)
router = APIRouter()

VALID_PERIODS = {"1W", "1M", "3M", "6M", "1Y", "2Y"}


@router.get("/chart/{ticker}")
async def get_chart(
    ticker: str = Path(..., description="Ticker symbol, e.g. AAPL"),
    period: str = Query("1M", description="1W | 1M | 3M | 6M | 1Y | 2Y"),
):
    """
    Returns OHLCV list:
        [{"date": "2024-01-02", "open": .., "high": .., "low": .., "close": .., "volume": ..}, ...]
    """
    ticker = ticker.upper().strip()
    period = period.upper().strip()
    if period not in VALID_PERIODS:
        period = "1M"

    candles = fetch_history(ticker, period)

    return JSONResponse({
        "ticker": ticker,
        "period": period,
        "candles": candles,
        "count":   len(candles),
    })
