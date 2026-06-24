# IVSURF Architecture

IVSURF is a quantitative research platform centered on **opening-hours volatility scanning** and swing signal research. Business logic lives in `engine/`; UI and HTTP layers are thin wrappers.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Presentation                            │
│  Streamlit (scripts/ivsurf_retro_terminal.py)  │  FastAPI (api/) │
│  app/components/*  app/styles/*                │  /scan /predict │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                         engine/                                 │
│  data/      fetcher, alpaca, storage, sessions, cache           │
│  features/  daily + intraday (gap, OR, VWAP, premarket)         │
│  signals/   opening_scanner, swing, regime_filter, ml_ranker    │
│  backtest/  labeling, walk_forward                              │
│  execution/ paper_trader (Alpaca)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Legacy quant libraries                       │
│  core/ models/ ml/ risk/ portfolio/ simulation/ visuals/        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      External data                              │
│  Yahoo Finance (default)  │  Alpaca (optional intraday + paper)│
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Opening Scanner

1. **Daily context** — `engine/features/daily.py` computes volatility, momentum, and price from Yahoo Finance daily bars.
2. **Intraday bars** — `engine/data/alpaca.py` fetches 1-min bars from Alpaca when credentials are set; falls back to yfinance.
3. **Feature engineering** — `engine/features/intraday.py` extracts gap %, premarket volume ratio, opening range, and relative volume.
4. **Regime filter** — `engine/signals/regime_filter.py` applies GARCH forecast and regime-switching multiplier to dampen scores in high-vol regimes.
5. **Scoring** — `engine/signals/opening_scanner.py` ranks tickers 0–100 via weighted heuristics.
6. **ML ranker** (optional) — `engine/signals/ml_ranker.py` re-ranks signals using walk-forward XGBoost on labeled outcomes.
7. **Labeling** — `engine/backtest/labeling.py` attaches 1h/1d/3d forward returns for backtest evaluation.

## Persistence

- SQLite schema in `engine/data/schema.sql`
- `engine/data/storage.py` writes scan results and signal history to `data/ivsurf.db` (configurable via `IVSURF_DB_PATH`)

## Entry Points

| Command | Purpose |
|---------|---------|
| `streamlit run scripts/ivsurf_retro_terminal.py` | Main UI |
| `uvicorn api.main:app --reload --port 8000` | REST API |
| `pytest` | Unit tests (integration tests marked separately) |

## Design Principles

- **Engine first** — No business logic in Streamlit callbacks; components call `engine/` functions.
- **Graceful degradation** — Optional deps (TensorFlow, arch, XGBoost, Alpaca) disable features rather than crash.
- **Research, not production** — Paper trading and heuristic scoring are for experimentation, not unattended live trading.

## Key Modules

| Module | Responsibility |
|--------|----------------|
| `engine/signals/opening_scanner.py` | Parallel universe scan, score aggregation |
| `engine/signals/swing.py` | Daily swing opportunity scoring (legacy scanner) |
| `engine/signals/ml_ranker.py` | Walk-forward ML re-ranking |
| `engine/execution/paper_trader.py` | Alpaca market order submission |
| `api/routes/scan.py` | HTTP wrapper for `scan_universe` |
| `app/components/opening_scanner_tab.py` | Streamlit scan UI |

## Testing Strategy

- Unit tests mock external APIs where possible (`dry_run` on paper trader).
- Integration tests (`pytest -m integration`) hit live Yahoo Finance; run manually in CI or locally with network.
