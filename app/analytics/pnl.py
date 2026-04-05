"""
app/analytics/pnl.py — P&L and portfolio-level calculations.

All functions are pure (no I/O) and easily unit-testable.
"""

from typing import Dict, List, Optional


def calc_holding(
    ticker:   str,
    shares:   float,
    avg_cost: float,
    quote:    Dict,
) -> Dict:
    """
    Merge a holding row with its live quote into a fully-enriched dict.

    Returns all fields needed by the frontend Holdings Table.
    """
    price        = quote.get("price") or 0
    change       = quote.get("change") or 0
    change_pct   = quote.get("change_pct") or 0
    div_yield    = quote.get("dividend_yield") or 0   # already as %

    cost_basis   = shares * avg_cost
    market_value = shares * price
    pnl_dollar   = market_value - cost_basis
    pnl_pct      = (pnl_dollar / cost_basis * 100) if cost_basis else 0
    day_change   = shares * change                    # dollar day change for this holding
    annual_div   = shares * price * (div_yield / 100) # estimated annual dividend income

    return {
        "ticker":        ticker,
        "shares":        shares,
        "avg_cost":      round(avg_cost, 4),
        "current_price": round(price, 4),
        "cost_basis":    round(cost_basis, 2),
        "market_value":  round(market_value, 2),
        "pnl_dollar":    round(pnl_dollar, 2),
        "pnl_pct":       round(pnl_pct, 4),
        "day_change":    round(day_change, 2),
        "day_change_pct":round(change_pct, 4),
        "div_yield":     round(div_yield, 4),
        "annual_div":    round(annual_div, 2),
        "pe_ratio":      quote.get("pe_ratio"),
        "week_52_high":  quote.get("week_52_high") or 0,
        "week_52_low":   quote.get("week_52_low") or 0,
        "market_cap":    quote.get("market_cap") or 0,
        "weight_pct":    0,           # filled in by calc_portfolio after totals known
        "source":        quote.get("source", "unknown"),
        "error":         quote.get("error"),
    }


def calc_portfolio(holdings: List[Dict]) -> Dict:
    """
    Given a list of enriched holding dicts (from calc_holding), compute
    portfolio-level KPI aggregates and fill in weight_pct per holding.

    Returns:
        {
          "kpis": {...},
          "holdings": [...],   # same list, weight_pct filled in
        }
    """
    total_invested    = sum(h["cost_basis"]   for h in holdings)
    total_market_val  = sum(h["market_value"] for h in holdings)
    total_pnl         = sum(h["pnl_dollar"]   for h in holdings)
    total_day_change  = sum(h["day_change"]    for h in holdings)
    total_annual_div  = sum(h["annual_div"]    for h in holdings)

    total_pnl_pct = (
        (total_pnl / total_invested * 100) if total_invested else 0
    )
    total_day_pct = (
        (total_day_change / (total_market_val - total_day_change) * 100)
        if (total_market_val - total_day_change)
        else 0
    )

    # fill weight_pct
    for h in holdings:
        h["weight_pct"] = round(
            (h["market_value"] / total_market_val * 100) if total_market_val else 0,
            2,
        )

    # best/worst performer by P&L %
    best = max(holdings, key=lambda h: h["pnl_pct"], default=None)
    worst = min(holdings, key=lambda h: h["pnl_pct"], default=None)

    kpis = {
        "total_invested":   round(total_invested, 2),
        "market_value":     round(total_market_val, 2),
        "total_pnl":        round(total_pnl, 2),
        "total_pnl_pct":    round(total_pnl_pct, 4),
        "day_change":       round(total_day_change, 2),
        "day_change_pct":   round(total_day_pct, 4),
        "total_annual_div": round(total_annual_div, 2),
        "best_performer":   best["ticker"] if best else None,
        "best_pnl_pct":     best["pnl_pct"] if best else 0,
        "worst_performer":  worst["ticker"] if worst else None,
        "worst_pnl_pct":    worst["pnl_pct"] if worst else 0,
    }

    return {"kpis": kpis, "holdings": holdings}
