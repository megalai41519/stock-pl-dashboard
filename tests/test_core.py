"""
tests/test_core.py — Unit tests for pure logic modules.

Run: pytest tests/ -v
"""

import pytest
import sys, os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── P&L calculations ─────────────────────────────────────────────────────────

from app.analytics.pnl import calc_holding, calc_portfolio


def _make_quote(price, change=0.0, change_pct=0.0, div_yield=0.0):
    return {
        "price": price, "change": change, "change_pct": change_pct,
        "dividend_yield": div_yield, "pe_ratio": None,
        "week_52_high": price * 1.2, "week_52_low": price * 0.8,
        "market_cap": 1_000_000_000, "source": "test", "error": None,
    }


class TestCalcHolding:
    def test_profit(self):
        h = calc_holding("AAPL", shares=10, avg_cost=100.0, quote=_make_quote(150.0))
        assert h["cost_basis"]   == 1000.00
        assert h["market_value"] == 1500.00
        assert h["pnl_dollar"]   == 500.00
        assert h["pnl_pct"]      == 50.0

    def test_loss(self):
        h = calc_holding("XYZ", shares=5, avg_cost=200.0, quote=_make_quote(150.0))
        assert h["pnl_dollar"] == -250.00
        assert h["pnl_pct"]    == -25.0

    def test_zero_price(self):
        h = calc_holding("BAD", shares=10, avg_cost=100.0, quote=_make_quote(0.0))
        assert h["market_value"] == 0.0
        assert h["pnl_dollar"]   == -1000.0

    def test_day_change_calc(self):
        h = calc_holding("MSFT", shares=4, avg_cost=200, quote=_make_quote(300, change=5.0))
        assert h["day_change"] == pytest.approx(20.0)   # 4 shares * $5

    def test_dividend_income(self):
        # 2% yield on $100 price × 10 shares = $20 annual
        h = calc_holding("T", shares=10, avg_cost=90, quote=_make_quote(100, div_yield=2.0))
        assert h["annual_div"] == pytest.approx(20.0)

    def test_weight_initially_zero(self):
        h = calc_holding("AAPL", shares=10, avg_cost=100, quote=_make_quote(150))
        assert h["weight_pct"] == 0   # filled later by calc_portfolio

    def test_fractional_shares(self):
        h = calc_holding("BRK", shares=0.5, avg_cost=400_000, quote=_make_quote(420_000))
        assert h["cost_basis"]   == pytest.approx(200_000)
        assert h["market_value"] == pytest.approx(210_000)
        assert h["pnl_dollar"]   == pytest.approx(10_000)


class TestCalcPortfolio:
    def _holdings(self):
        return [
            calc_holding("AAPL", 10, 100, _make_quote(150, change=2, change_pct=1.4)),
            calc_holding("MSFT", 5,  200, _make_quote(180, change=-3, change_pct=-1.6)),
        ]

    def test_total_invested(self):
        result = calc_portfolio(self._holdings())
        assert result["kpis"]["total_invested"] == pytest.approx(2000.0)

    def test_market_value(self):
        result = calc_portfolio(self._holdings())
        # AAPL: 10*150=1500, MSFT: 5*180=900
        assert result["kpis"]["market_value"] == pytest.approx(2400.0)

    def test_total_pnl(self):
        result = calc_portfolio(self._holdings())
        # AAPL: +500, MSFT: -100  → +400
        assert result["kpis"]["total_pnl"] == pytest.approx(400.0)

    def test_weight_pct_sums_to_100(self):
        result = calc_portfolio(self._holdings())
        total_weight = sum(h["weight_pct"] for h in result["holdings"])
        assert total_weight == pytest.approx(100.0, abs=0.05)

    def test_best_performer(self):
        result = calc_portfolio(self._holdings())
        kpis = result["kpis"]
        assert kpis["best_performer"] == "AAPL"

    def test_worst_performer(self):
        result = calc_portfolio(self._holdings())
        assert result["kpis"]["worst_performer"] == "MSFT"

    def test_holdings_count_preserved(self):
        result = calc_portfolio(self._holdings())
        assert len(result["holdings"]) == 2

    def test_empty_portfolio(self):
        result = calc_portfolio([])
        assert result["kpis"]["total_invested"] == 0
        assert result["kpis"]["best_performer"] is None


# ── CSV loader ────────────────────────────────────────────────────────────────

import csv, tempfile, pathlib
from unittest.mock import patch
from app.data.loader import load_portfolio, PortfolioLoadError


def _write_csv(rows: list[dict], path: str):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["stock_name","total_shares","cost_at_buy"])
        writer.writeheader()
        writer.writerows(rows)


class TestLoadPortfolio:
    def test_valid_csv(self, tmp_path):
        csv_file = str(tmp_path / "portfolio.csv")
        _write_csv([
            {"stock_name": "AAPL", "total_shares": "10", "cost_at_buy": "145.50"},
            {"stock_name": "msft", "total_shares": "5",  "cost_at_buy": "280.00"},
        ], csv_file)

        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            holdings = load_portfolio()

        assert len(holdings) == 2
        assert holdings[0]["ticker"] == "AAPL"
        assert holdings[0]["shares"] == 10.0
        assert holdings[0]["avg_cost"] == 145.50
        assert holdings[1]["ticker"] == "MSFT"   # lowercased ticker is uppercased

    def test_missing_file_raises(self, tmp_path):
        with patch("app.data.loader.PORTFOLIO_CSV", str(tmp_path / "no_file.csv")):
            with pytest.raises(PortfolioLoadError, match="not found"):
                load_portfolio()

    def test_missing_column_raises(self, tmp_path):
        csv_file = str(tmp_path / "bad.csv")
        with open(csv_file, "w") as f:
            f.write("ticker,shares\nAAPL,10\n")
        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            with pytest.raises(PortfolioLoadError, match="missing required columns"):
                load_portfolio()

    def test_invalid_shares_skipped(self, tmp_path):
        csv_file = str(tmp_path / "portfolio.csv")
        _write_csv([
            {"stock_name": "AAPL", "total_shares": "abc", "cost_at_buy": "145"},
            {"stock_name": "MSFT", "total_shares": "5",   "cost_at_buy": "280"},
        ], csv_file)
        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            holdings = load_portfolio()
        assert len(holdings) == 1
        assert holdings[0]["ticker"] == "MSFT"

    def test_zero_shares_skipped(self, tmp_path):
        csv_file = str(tmp_path / "portfolio.csv")
        _write_csv([
            {"stock_name": "AAPL", "total_shares": "0", "cost_at_buy": "145"},
        ], csv_file)
        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            with pytest.raises(PortfolioLoadError):
                load_portfolio()

    def test_comma_in_numbers(self, tmp_path):
        csv_file = str(tmp_path / "portfolio.csv")
        _write_csv([
            {"stock_name": "BRK", "total_shares": "1,000", "cost_at_buy": "350,000.00"},
        ], csv_file)
        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            holdings = load_portfolio()
        assert holdings[0]["shares"]   == 1000.0
        assert holdings[0]["avg_cost"] == 350000.0

    def test_utf8_bom_header(self, tmp_path):
        """CSV exported from Excel often has a UTF-8 BOM — must still parse."""
        csv_file = str(tmp_path / "portfolio.csv")
        with open(csv_file, "w", encoding="utf-8-sig") as f:
            f.write("stock_name,total_shares,cost_at_buy\nAAPL,10,150\n")
        with patch("app.data.loader.PORTFOLIO_CSV", csv_file):
            holdings = load_portfolio()
        assert holdings[0]["ticker"] == "AAPL"


# ── Cache ─────────────────────────────────────────────────────────────────────

import time
from unittest.mock import patch as mock_patch
from app.data import cache as cache_module


class TestCache:
    def setup_method(self):
        """Use a fresh in-memory-like temp db per test."""
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._patcher = mock_patch("app.data.cache.CACHE_DB", self._tmp.name)
        self._patcher.start()
        cache_module.init_cache()

    def teardown_method(self):
        self._patcher.stop()
        pathlib.Path(self._tmp.name).unlink(missing_ok=True)

    def test_set_and_get(self):
        cache_module.set("key1", {"foo": "bar"})
        result = cache_module.get("key1")
        assert result == {"foo": "bar"}

    def test_miss_returns_none(self):
        assert cache_module.get("nonexistent") is None

    def test_expired_returns_none(self):
        cache_module.set("expiring", 42)
        with mock_patch("app.data.cache.CACHE_TTL_SEC", -1):
            assert cache_module.get("expiring") is None

    def test_overwrite(self):
        cache_module.set("k", "v1")
        cache_module.set("k", "v2")
        assert cache_module.get("k") == "v2"

    def test_invalidate(self):
        cache_module.set("del_me", "value")
        cache_module.invalidate("del_me")
        assert cache_module.get("del_me") is None

    def test_list_types(self):
        cache_module.set("list_key", [1, 2, 3])
        assert cache_module.get("list_key") == [1, 2, 3]

    def test_purge_expired(self):
        cache_module.set("old", "data")
        with mock_patch("app.data.cache.CACHE_TTL_SEC", -1):
            removed = cache_module.purge_expired()
        assert removed >= 1
        assert cache_module.get("old") is None
