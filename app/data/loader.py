"""
app/data/loader.py — reads and validates portfolio.csv.

Expected columns (case-insensitive):
    stock_name, total_shares, cost_at_buy

Returns a list of dicts:
    [{"ticker": "AAPL", "shares": 10.0, "avg_cost": 150.00}, ...]
"""

import csv
import os
import logging
from typing import List, Dict

from app.config import PORTFOLIO_CSV

log = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"stock_name", "total_shares", "cost_at_buy"}


class PortfolioLoadError(Exception):
    pass


def detect_csv_issues() -> dict:
    """
    Inspect the raw CSV file for signs it was exported from Apple Numbers
    in the wrong format (.numbers opened and re-saved, or exported with
    rich formatting artifacts).

    Returns a dict of detected issue flags.
    """
    issues = {"numbers_format": False}

    if not os.path.exists(PORTFOLIO_CSV):
        return issues

    try:
        with open(PORTFOLIO_CSV, "rb") as f:
            raw = f.read(512)

        # Apple Numbers plain-CSV export is usually clean UTF-8 or UTF-8-BOM.
        # The .numbers binary format starts with a PK zip header.
        if raw[:2] == b"PK":
            issues["numbers_format"] = True
            log.warning(
                "portfolio.csv appears to be a .numbers binary file, not plain CSV. "
                "In Numbers: File → Export To → CSV."
            )

        # Another sign: null bytes in first 512 bytes (binary format)
        elif b"\x00" in raw:
            issues["numbers_format"] = True
            log.warning("portfolio.csv contains binary data — export as plain CSV.")

    except OSError:
        pass

    return issues



    """Read portfolio.csv and return validated holding rows."""

    if not os.path.exists(PORTFOLIO_CSV):
        raise PortfolioLoadError(
            f"portfolio.csv not found at: {PORTFOLIO_CSV}\n"
            "Place portfolio.csv in the same folder as the application."
        )

    holdings: List[Dict] = []
    errors: List[str] = []

    with open(PORTFOLIO_CSV, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)

        # Normalise header names
        if reader.fieldnames is None:
            raise PortfolioLoadError("portfolio.csv appears to be empty.")

        normalised = {col.strip().lower(): col for col in reader.fieldnames}
        missing = REQUIRED_COLUMNS - set(normalised.keys())
        if missing:
            raise PortfolioLoadError(
                f"portfolio.csv is missing required columns: {missing}\n"
                "Expected: stock_name, total_shares, cost_at_buy"
            )

        for i, row in enumerate(reader, start=2):  # row 1 = header
            # Map to normalised keys
            norm_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            ticker    = norm_row.get("stock_name", "").upper().strip()
            shares_s  = norm_row.get("total_shares", "")
            cost_s    = norm_row.get("cost_at_buy", "")

            if not ticker:
                errors.append(f"Row {i}: empty stock_name — skipped.")
                continue

            try:
                shares = float(shares_s.replace(",", ""))
            except ValueError:
                errors.append(f"Row {i} ({ticker}): invalid total_shares '{shares_s}' — skipped.")
                continue

            try:
                avg_cost = float(cost_s.replace(",", ""))
            except ValueError:
                errors.append(f"Row {i} ({ticker}): invalid cost_at_buy '{cost_s}' — skipped.")
                continue

            if shares <= 0:
                errors.append(f"Row {i} ({ticker}): total_shares must be > 0 — skipped.")
                continue

            if avg_cost < 0:
                errors.append(f"Row {i} ({ticker}): cost_at_buy must be >= 0 — skipped.")
                continue

            holdings.append({"ticker": ticker, "shares": shares, "avg_cost": avg_cost})

    for err in errors:
        log.warning(err)

    if not holdings:
        raise PortfolioLoadError(
            "No valid holdings found in portfolio.csv.\n"
            + "\n".join(errors)
        )

    log.info("Loaded %d holdings from portfolio.csv", len(holdings))
    return holdings
