"""
app/routes/news.py

GET /api/news/{ticker}  → latest headlines for a single ticker.
"""

import logging
from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

from app.data.fetcher import fetch_news

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/news/{ticker}")
async def get_news(
    ticker: str = Path(..., description="Ticker symbol, e.g. AAPL"),
    limit:  int = Query(8, ge=1, le=20, description="Number of headlines"),
):
    """
    Returns:
        {
          "ticker": "AAPL",
          "articles": [
            {"title": .., "url": .., "source": .., "published": .., "summary": ..},
            ...
          ]
        }
    """
    ticker = ticker.upper().strip()
    articles = fetch_news(ticker, limit)
    return JSONResponse({"ticker": ticker, "articles": articles})
