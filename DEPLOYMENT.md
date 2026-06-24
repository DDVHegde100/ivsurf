# Deployment

## Streamlit UI (Community Cloud)

1. Fork [ivsurf](https://github.com/DDVHegde100/ivsurf)
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Connect GitHub and select your fork
4. Set main file: `scripts/ivsurf_retro_terminal.py`
5. Deploy

### Streamlit secrets (optional)

For intraday bars and paper trading, add secrets in the Streamlit dashboard:

```toml
ALPACA_API_KEY = "your-key"
ALPACA_SECRET_KEY = "your-secret"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

Without Alpaca credentials the opening scanner falls back to yfinance 1-min data (limited history).

## FastAPI

Run locally or deploy to any ASGI host (Railway, Fly.io, Render):

```bash
pip install -e ".[api]"
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/scan` | Run opening scanner on ticker list |
| GET | `/predict/{ticker}` | Single-ticker scan + ML rank |
| GET | `/signals/history` | Stored signal history from SQLite |

Set the same Alpaca and database env vars as the Streamlit app.

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ALPACA_API_KEY` | No | — | Alpaca API key |
| `ALPACA_SECRET_KEY` | No | — | Alpaca secret |
| `ALPACA_BASE_URL` | No | `https://paper-api.alpaca.markets` | Paper or live API base |
| `IVSURF_DB_PATH` | No | `data/ivsurf.db` | SQLite database path |
| `IVSURF_API_KEY` | No | — | When set, protected routes require `X-API-Key` header |
| `IVSURF_DATABASE_URL` | No | — | PostgreSQL URL; when set, replaces SQLite for signals/bars |
| `IVSURF_DATA_DIR` | No | `data` | Directory for Parquet exports when using Postgres |

Copy `.env.example` to `.env` for local development.

### API authentication

When `IVSURF_API_KEY` is set, `/scan`, `/predict`, and `/signals` require the header:

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/signals/history
```

`/health` stays public and reports `"auth": "required"` or `"disabled"`. Leave `IVSURF_API_KEY` unset for local development without auth.

### PostgreSQL storage

For multiple API replicas or shared signal history, point all instances at the same database:

```bash
pip install -e ".[postgres]"
export IVSURF_DATABASE_URL=postgresql://user:pass@host:5432/ivsurf
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Tables are created automatically on startup. When `IVSURF_DATABASE_URL` is unset, IVSURF uses SQLite at `IVSURF_DB_PATH` (default `data/ivsurf.db`).

### ML ranker training

After signals accumulate outcome labels in the database, retrain the opening ranker:

```bash
python scripts/train_ml_ranker.py --horizon 1h --min-samples 30
```

The model is saved to `data/models/opening_ranker.joblib` (override with `IVSURF_MODEL_PATH`). The Opening Scanner tab and `/predict` endpoint apply ML re-ranking when this file exists.

### Webhook alerts

Notify Slack or Discord when scan hits exceed a score threshold:

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
export IVSURF_ALERT_MIN_SCORE=50

python scripts/run_premarket_scan.py --alert --alert-threshold 50
```

The pre-market GitHub Action passes `--alert` automatically when webhook secrets are configured. Use `--alert-dry-run` to preview payloads locally.

### Trading guardrails

Paper and live Alpaca orders pass through pre-trade guardrails:

| Variable | Default | Purpose |
|----------|---------|---------|
| `IVSURF_GUARDRAILS_ENABLED` | `true` | Toggle all guardrails |
| `IVSURF_MAX_DAILY_LOSS_PCT` | `2` | Block orders when daily P&L falls below this % |
| `IVSURF_MAX_OPEN_POSITIONS` | `5` | Max concurrent open positions |
| `IVSURF_MAX_ORDERS_PER_DAY` | `10` | Max orders submitted per session/day |
| `IVSURF_MAX_NOTIONAL_PER_TRADE` | `1000` | Cap per-order notional |
| `IVSURF_ONE_POSITION_PER_SYMBOL` | `true` | Prevent duplicate symbol exposure |

Blocked orders return `status: blocked` with a reason in the Opening Scanner order execution panel.

### Broker adapters

Execution uses a pluggable broker interface:

| Broker | `IVSURF_BROKER` | Notes |
|--------|-----------------|-------|
| Alpaca | `alpaca` (default) | Paper or live via `ALPACA_BASE_URL` |
| Simulated | `simulated` | Local dry-run with in-memory positions |

```python
from engine.execution import create_executor

executor = create_executor("simulated")
executor.execute_signal({"ticker": "AAPL", "opening_score": 80, "price": 100, "direction": "up"})
```

## Scheduled Pre-market Scan

A GitHub Action runs the opening scanner on weekdays at **13:00 UTC** (~8:00 AM EST / 9:00 AM EDT):

- Workflow: [`.github/workflows/premarket_scan.yml`](.github/workflows/premarket_scan.yml)
- Manual trigger: **Actions → Pre-market Scan → Run workflow**
- Optional secrets: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_BASE_URL` (for 1-min bars)
- Results uploaded as workflow artifacts (`premarket_scan.json`)

Run locally:

```bash
python scripts/run_premarket_scan.py --force --output data/premarket_scan.json
```

Use `--force` on weekends; omit it to skip non-trading days.

Preset universes: `core`, `opening`, `tech_mega`, `semis`, `finance`, `energy`, `etfs`, `high_beta`.

```bash
python scripts/run_premarket_scan.py --universe semis --min-score 20
python scripts/run_premarket_scan.py --universe user:my_watchlist
```

## Docker

If a `Dockerfile` is present in the repo root:

```bash
docker build -t ivsurf .
docker run -p 8503:8503 -e ALPACA_API_KEY=... ivsurf
```

## Resources

- Streamlit Community Cloud: 1 GB RAM, shared CPU — sufficient for scanner workloads on small universes (<50 tickers).
- FastAPI: stateless; scale horizontally. SQLite is single-writer; use Postgres for multi-instance deployments.

## Production Checklist

- [ ] Use Alpaca **paper** credentials until strategies are validated
- [ ] Set `min_score` conservatively on automated paper trading
- [ ] Do not expose the API publicly without authentication
- [ ] Monitor Yahoo Finance rate limits on large scans
