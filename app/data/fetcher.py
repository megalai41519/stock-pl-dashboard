"""
app/data/fetcher.py — market data fetching.

Primary  : Financial Modeling Prep (FMP) free tier
Fallback : yfinance with browser-spoof headers + retry/backoff

All public functions cache results automatically.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any

import requests
import yfinance as yf

from app.config import (
    FMP_BASE_URL,
    RETRY_ATTEMPTS,
    RETRY_DELAYS,
    YFINANCE_HEADERS,
)
from app.data import cache

log = logging.getLogger(__name__)

# ── Global warning flags (reset each process run) ────────────────────────────
_warnings: Dict[str, bool] = {
    "fmp_rate_limited": False,   # FMP 429 or daily limit hit
    "yfinance_fallback": False,  # fell back to yfinance for any ticker
}


# ── Public: read accumulated warnings ────────────────────────────────────────

def get_warnings() -> Dict[str, bool]:
    """Return a snapshot of active warning flags for the current session."""
    return dict(_warnings)


def clear_warnings() -> None:
    """Reset all warning flags (called on manual refresh)."""
    _warnings["fmp_rate_limited"] = False
    _warnings["yfinance_fallback"] = False


# ── helpers ───────────────────────────────────────────────────────────────────

def _fmp_key() -> Optional[str]:
    return os.getenv("FMP_API_KEY")


def _fmp_get(endpoint: str, params: Dict = {}) -> Optional[Any]:
    """GET from FMP with retry/backoff. Returns parsed JSON or None."""
    key = _fmp_key()
    if not key:
        log.warning("FMP_API_KEY not set — skipping FMP call.")
        return None

    url = f"{FMP_BASE_URL}/{endpoint}"
    params = {**params, "apikey": key}

    for attempt in range(RETRY_ATTEMPTS):
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 429:
                log.warning("FMP rate-limited (429) on attempt %d", attempt + 1)
                _warnings["fmp_rate_limited"] = True
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAYS[attempt])
                continue
            r.raise_for_status()
            data = r.json()
            # FMP returns {"Error Message": "..."} on bad key / limit exceeded
            if isinstance(data, dict) and "Error Message" in data:
                log.error("FMP error: %s", data["Error Message"])
                if "limit" in data["Error Message"].lower() or "exceed" in data["Error Message"].lower():
                    _warnings["fmp_rate_limited"] = True
                return None
            return data
        except requests.RequestException as exc:
            log.warning("FMP request failed (attempt %d): %s", attempt + 1, exc)
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAYS[attempt])

    return None


def _yf_ticker(symbol: str) -> yf.Ticker:
    t = yf.Ticker(symbol)
    # inject browser-spoof session headers
    t._download_options = {}
    session = requests.Session()
    session.headers.update(YFINANCE_HEADERS)
    t.session = session
    return t


# ── quote (current price, day change, etc.) ───────────────────────────────────

def fetch_quote(ticker: str) -> Dict:
    """
    Returns:
        price, change, change_pct, volume, market_cap,
        pe_ratio, week_52_high, week_52_low, dividend_yield
    """
    cache_key = f"quote:{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    result = _fetch_quote_fmp(ticker) or _fetch_quote_yf(ticker) or _empty_quote(ticker)
    if result.get("source") == "yfinance":
        _warnings["yfinance_fallback"] = True
    cache.set(cache_key, result)
    return result


def _fetch_quote_fmp(ticker: str) -> Optional[Dict]:
    data = _fmp_get(f"quote/{ticker}")
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    q = data[0]
    return {
        "ticker":         ticker,
        "price":          q.get("price") or 0,
        "change":         q.get("change") or 0,
        "change_pct":     q.get("changesPercentage") or 0,
        "volume":         q.get("volume") or 0,
        "market_cap":     q.get("marketCap") or 0,
        "pe_ratio":       q.get("pe") or None,
        "week_52_high":   q.get("yearHigh") or 0,
        "week_52_low":    q.get("yearLow") or 0,
        "dividend_yield": q.get("lastAnnualDividend", 0) / q.get("price", 1) * 100
                          if q.get("price") else 0,
        "source":         "fmp",
        "error":          None,
    }


def _fetch_quote_yf(ticker: str) -> Optional[Dict]:
    try:
        t = _yf_ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        prev  = info.get("previousClose") or price
        change     = price - prev
        change_pct = (change / prev * 100) if prev else 0
        div_yield  = (info.get("dividendYield") or 0) * 100
        return {
            "ticker":         ticker,
            "price":          price,
            "change":         change,
            "change_pct":     change_pct,
            "volume":         info.get("volume") or 0,
            "market_cap":     info.get("marketCap") or 0,
            "pe_ratio":       info.get("trailingPE") or None,
            "week_52_high":   info.get("fiftyTwoWeekHigh") or 0,
            "week_52_low":    info.get("fiftyTwoWeekLow") or 0,
            "dividend_yield": div_yield,
            "source":         "yfinance",
            "error":          None,
        }
    except Exception as exc:
        log.error("yfinance quote failed for %s: %s", ticker, exc)
        return None


def _empty_quote(ticker: str) -> Dict:
    return {
        "ticker": ticker, "price": 0, "change": 0, "change_pct": 0,
        "volume": 0, "market_cap": 0, "pe_ratio": None,
        "week_52_high": 0, "week_52_low": 0, "dividend_yield": 0,
        "source": "none", "error": f"Could not fetch data for {ticker}",
    }


# ── price history (candlestick) ───────────────────────────────────────────────

_PERIOD_DAYS = {"1W": 7, "1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730}
_YF_PERIOD   = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y"}
_YF_INTERVAL = {"1W": "1h", "1M": "1d", "3M": "1d", "6M": "1d", "1Y": "1wk", "2Y": "1wk"}


def fetch_history(ticker: str, period: str = "1M") -> List[Dict]:
    """
    Returns a list of OHLCV candles:
        [{"date": "2024-01-02", "open": .., "high": .., "low": .., "close": .., "volume": ..}, ...]
    """
    period = period.upper()
    if period not in _PERIOD_DAYS:
        period = "1M"

    cache_key = f"history:{ticker}:{period}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = _fetch_history_fmp(ticker, period) or _fetch_history_yf(ticker, period) or []
    cache.set(cache_key, data)
    return data


def _fetch_history_fmp(ticker: str, period: str) -> Optional[List[Dict]]:
    days = _PERIOD_DAYS[period]
    limit = max(days, 730)
    raw = _fmp_get(f"historical-price-full/{ticker}", {"timeseries": limit})
    if not raw or "historical" not in raw:
        return None

    rows = raw["historical"]
    # FMP returns newest-first
    rows = list(reversed(rows))

    # Trim to requested period
    if len(rows) > days * 2:
        rows = rows[-(days * 2):]

    candles = []
    for r in rows:
        candles.append({
            "date":   r.get("date", ""),
            "open":   r.get("open") or 0,
            "high":   r.get("high") or 0,
            "low":    r.get("low") or 0,
            "close":  r.get("close") or 0,
            "volume": r.get("volume") or 0,
        })
    return candles if candles else None


def _fetch_history_yf(ticker: str, period: str) -> Optional[List[Dict]]:
    try:
        t = _yf_ticker(ticker)
        df = t.history(period=_YF_PERIOD[period], interval=_YF_INTERVAL[period])
        if df.empty:
            return None
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "date":   str(idx.date()),
                "open":   round(float(row["Open"]), 4),
                "high":   round(float(row["High"]), 4),
                "low":    round(float(row["Low"]), 4),
                "close":  round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            })
        return candles
    except Exception as exc:
        log.error("yfinance history failed for %s: %s", ticker, exc)
        return None


# ── news ──────────────────────────────────────────────────────────────────────

def fetch_news(ticker: str, limit: int = 8) -> List[Dict]:
    """
    Returns latest news headlines:
        [{"title": .., "url": .., "source": .., "published": ..}, ...]
    """
    cache_key = f"news:{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = _fetch_news_fmp(ticker, limit) or _fetch_news_yf(ticker, limit) or []
    cache.set(cache_key, data)
    return data


def _fetch_news_fmp(ticker: str, limit: int) -> Optional[List[Dict]]:
    raw = _fmp_get("stock_news", {"tickers": ticker, "limit": limit})
    if not raw or not isinstance(raw, list):
        return None
    out = []
    for item in raw[:limit]:
        out.append({
            "title":     item.get("title", ""),
            "url":       item.get("url", ""),
            "source":    item.get("site", ""),
            "published": item.get("publishedDate", ""),
            "summary":   item.get("text", "")[:200] if item.get("text") else "",
        })
    return out if out else None


def _fetch_news_yf(ticker: str, limit: int) -> Optional[List[Dict]]:
    try:
        t = _yf_ticker(ticker)
        raw = t.news or []
        out = []
        for item in raw[:limit]:
            out.append({
                "title":     item.get("title", ""),
                "url":       item.get("link", ""),
                "source":    item.get("publisher", ""),
                "published": item.get("providerPublishTime", ""),
                "summary":   "",
            })
        return out if out else None
    except Exception as exc:
        log.error("yfinance news failed for %s: %s", ticker, exc)
        return None
