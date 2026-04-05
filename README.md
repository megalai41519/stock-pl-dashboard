# 📈 Stock P&L Dashboard

A production-grade personal portfolio analytics dashboard that runs entirely on your local machine. No cloud, no subscriptions, no monthly fees — **$0 forever**.

![Dashboard Preview](https://img.shields.io/badge/status-production%20ready-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

---

## ✨ Features

| Feature | Details |
|---|---|
| **KPI Cards** | Total Invested, Market Value, Total P&L, Day Change, Best Performer |
| **Holdings Table** | Shares, Avg Cost, Current Price, Cost Basis, Market Value, P&L $, P&L %, Day Change, Weight %, Dividend Yield |
| **Candlestick Chart** | Interactive price history with 1W/1M/3M/6M/1Y/2Y tabs |
| **Allocation Donut** | Portfolio weight by market value |
| **Dividend Income** | Estimated annual dividend bar chart |
| **News Panel** | Per-ticker headlines (click any holding row) |
| **15-min Cache** | SQLite cache — no repeated API calls |
| **Auto Fallback** | FMP → yfinance automatic fallback |

---

## 🚀 Quick Start (Development)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/stock-pl-dashboard.git
cd stock-pl-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a free FMP API key

1. Go to [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)
2. Click **"Get My Free API Key"**
3. Sign up with your email — **no credit card required**
4. Copy your API key from the dashboard

> **Free tier limits:** 250 requests/day. The 15-minute cache ensures you won't burn through this quickly. For a 5-stock portfolio, a full refresh uses ~25 requests.

### 5. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder:

```env
FMP_API_KEY=your_actual_key_here
```

### 6. Create your `portfolio.csv`

```csv
stock_name,total_shares,cost_at_buy
AAPL,10,145.50
MSFT,5,280.00
GOOGL,3,130.25
AMZN,4,175.00
NVDA,8,450.00
```

- `stock_name` — NYSE/NASDAQ ticker symbol (case-insensitive)
- `total_shares` — number of shares owned (decimals allowed)
- `cost_at_buy` — your average purchase price per share

### 7. Run the dashboard

```bash
python main.py
```

Your browser opens automatically at **http://localhost:8000**

---

## 📁 Project Structure

```
stock-pl-dashboard/
├── main.py                        ← FastAPI entry point + browser launch
├── portfolio.csv                  ← your holdings (gitignored)
├── .env                           ← FMP_API_KEY (gitignored)
├── requirements.txt
├── .gitignore
├── README.md
├── app/
│   ├── config.py                  ← paths, settings, TTL
│   ├── data/
│   │   ├── loader.py              ← CSV reader & validator
│   │   ├── fetcher.py             ← FMP primary, yfinance fallback
│   │   └── cache.py               ← SQLite cache (15-min TTL)
│   ├── analytics/
│   │   └── pnl.py                 ← P&L calculations (pure functions)
│   └── routes/
│       ├── portfolio.py           ← GET /api/portfolio
│       ├── charts.py              ← GET /api/chart/{ticker}
│       └── news.py                ← GET /api/news/{ticker}
├── frontend/
│   └── index.html                 ← full dashboard UI (Plotly.js)
├── build/
│   ├── stock_dashboard_mac.spec
│   ├── stock_dashboard_win.spec
│   ├── build_mac.sh
│   └── build_windows.ps1
├── tests/
│   └── test_core.py               ← unit tests (pytest)
└── .github/
    └── workflows/
        └── release.yml            ← auto-build on git tag push
```

---

## 🖥️ Packaged App (No Python Required)

Pre-built binaries are available on the [Releases page](https://github.com/YOUR_USERNAME/stock-pl-dashboard/releases).

### Download and run

1. Download the zip for your platform from the latest release
2. Unzip it
3. Create `portfolio.csv` and `.env` (see format above)
4. Place both files **next to** the app/exe
5. Run (see platform notes below)

---

### 🍎 macOS Notes

> **Critical:** Move `StockDashboard.app` out of your Downloads folder before running.
> macOS App Translocation will prevent it from finding `portfolio.csv` otherwise.

**First run (Gatekeeper bypass):**
```bash
# Option A: Right-click → Open
# Option B: Remove quarantine flag
xattr -cr StockDashboard.app
```

**File layout:**
```
~/Desktop/StockDashboard/
├── StockDashboard.app
├── portfolio.csv
└── .env
```

---

### 🪟 Windows Notes

**SmartScreen warning** (unsigned app):
1. Click **"More info"**
2. Click **"Run anyway"**

**File layout:**
```
C:\Users\You\StockDashboard\
├── StockDashboard.exe
├── portfolio.csv
└── .env
```

---

## 🏗️ Build from Source

### macOS

```bash
bash build/build_mac.sh
# Output: dist/mac/StockDashboard.app
```

### Windows

```powershell
.\build\build_windows.ps1
# Output: dist\windows\StockDashboard.exe
```

---

## 🚢 Release to GitHub

Releases are built automatically by GitHub Actions when you push a version tag.

### One-time setup

1. Go to your repo → **Settings → Actions → General**
2. Under **Workflow permissions**, select **"Read and write permissions"**
3. Click **Save**

### Publishing a release

```bash
git add .
git commit -m "feat: add new feature"
git tag v1.0.0
git push origin main --tags
```

GitHub Actions will:
1. Build `StockDashboard.app` on `macos-latest`
2. Build `StockDashboard.exe` on `windows-latest`
3. Create a GitHub Release with both files and install instructions

---

## 🔌 API Reference

All endpoints served at `http://localhost:8000`

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/portfolio` | GET | Full portfolio: KPIs + holdings |
| `POST /api/portfolio/refresh` | POST | Bust cache, force fresh data |
| `GET /api/chart/{ticker}?period=1M` | GET | OHLCV candlestick data |
| `GET /api/news/{ticker}?limit=8` | GET | Latest news headlines |
| `GET /health` | GET | Health check |

**Valid periods:** `1W`, `1M`, `3M`, `6M`, `1Y`, `2Y`

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:
- P&L calculations (profit, loss, fractional shares, dividends)
- Portfolio aggregation (totals, weights, best/worst performer)
- CSV loading (validation, error handling, BOM encoding, commas in numbers)
- Cache layer (set/get, TTL expiry, invalidation, purge)

---

## 📊 Data Sources

### Primary: Financial Modeling Prep (FMP)

- **Free tier:** 250 requests/day, no credit card
- **Sign up:** [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)
- Provides: price quotes, P/E ratio, dividend yield, OHLCV history, news

### Fallback: yfinance

- Completely free, unofficial Yahoo Finance wrapper
- Automatically used if FMP fails or rate-limits
- Browser-spoof headers + exponential backoff retry

### Cache

- SQLite `cache.db` stored next to the executable
- 15-minute TTL — delete `cache.db` to force fresh data
- Thread-safe, auto-created on first run

---

## ⚙️ Configuration

All settings are in `app/config.py`:

| Setting | Default | Description |
|---|---|---|
| `CACHE_TTL_SEC` | `900` (15 min) | Cache time-to-live |
| `RETRY_ATTEMPTS` | `3` | Max API retry attempts |
| `RETRY_DELAYS` | `[2, 4, 8]` | Seconds between retries (backoff) |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `portfolio.csv not found` | Place `portfolio.csv` next to the `.app` / `.exe` (not inside it) |
| `FMP_API_KEY not set` | Create `.env` with `FMP_API_KEY=your_key` next to the app |
| Red error banner: rate limit | FMP free tier hit 250/day limit; data served from yfinance fallback |
| Mac: "App is damaged" | Run `xattr -cr StockDashboard.app` in Terminal |
| Mac: can't find CSV | Move app out of Downloads (App Translocation issue) |
| Windows: blocked by SmartScreen | Click "More info" → "Run anyway" |
| `$0` prices showing | Check your FMP key is valid; delete `cache.db` and refresh |
| Port 8000 already in use | Kill the existing process: `lsof -ti:8000 \| xargs kill` |

---

## 💰 Cost Breakdown

| Component | Cost |
|---|---|
| FMP API (free tier) | $0/month |
| yfinance fallback | $0/month |
| GitHub Actions CI/CD | $0/month (public repo) |
| PyInstaller packaging | $0 |
| Hosting | $0 (runs locally) |
| **Total** | **$0 forever** |

---

## 📋 portfolio.csv Format

```csv
stock_name,total_shares,cost_at_buy
AAPL,10,145.50
MSFT,5,280.00
GOOGL,3,130.25
```

**Rules:**
- Headers must be exactly: `stock_name`, `total_shares`, `cost_at_buy`
- Tickers: US market symbols only (NYSE/NASDAQ)
- Shares: positive number (decimals OK, e.g. `0.5`)
- Cost: your average purchase price per share in USD
- Numbers may include commas (e.g. `1,000`)
- **Mac users:** Export as plain CSV from TextEdit, not Numbers `.numbers` format

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built with FastAPI · Plotly.js · SQLite · yfinance · Financial Modeling Prep*
