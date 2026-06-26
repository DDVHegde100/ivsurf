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
| WS | `/ws/opening-range` | Live opening-range snapshots (see below) |
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

WebSocket clients pass the same key as a query parameter:

```bash
websocat "ws://localhost:8000/ws/opening-range?api_key=your-key"
```

### Opening range websocket

Subscribe after connecting:

```json
{"action": "subscribe", "tickers": ["AAPL", "NVDA"], "interval_sec": 30}
```

The server responds with `subscribed`, then periodic `update` messages containing 5m/15m/30m opening-range high, low, range %, volume, and breakout status. Default poll interval is controlled by `IVSURF_OR_FEED_INTERVAL_SEC` (30 seconds).

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

One-command deploy (Streamlit UI + FastAPI):

```bash
cp .env.example .env   # optional: add Alpaca keys, IVSURF_API_KEY
./scripts/compose-up.sh
```

Or manually:

```bash
docker compose up -d --build
```

| Service | URL | Description |
|---------|-----|-------------|
| `ui` | http://localhost:8501 | Streamlit terminal |
| `api` | http://localhost:8000/health | FastAPI backend |

Shared signal data persists in the `ivsurf_data` Docker volume at `/app/data`.

Optional PostgreSQL backend:

```bash
./scripts/compose-up.sh --postgres
# or
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d --build
```

Stop all services:

```bash
docker compose down
```

## Vercel (OpenPulse API)

Deploy the **FastAPI backend** and static landing page to Vercel:

```bash
npm i -g vercel   # or npx vercel
vercel link       # first time only
vercel --prod
```

Or push to `main` if the GitHub repo is connected to Vercel.

| Route | Description |
|-------|-------------|
| `/` | OpenPulse landing page (`public/index.html`) |
| `/health` | API health check |
| `/scan` | Opening scanner (POST) |
| `/spatial/catalog` | 3D spatial asset catalog |
| `/spatial/heston` | Heston IV grid JSON |

**Notes:**

- Vercel uses `requirements-vercel.txt` (slim deps, no Streamlit).
- Entry point: `api/index.py` exports the FastAPI ASGI app.
- WebSocket `/ws/opening-range` is **not** supported on Vercel serverless.
- Set env vars in the Vercel dashboard: `IVSURF_API_KEY`, `ALPACA_API_KEY`, etc.
- Full Streamlit terminal remains on Streamlit Cloud or Docker.

## Resources

- Streamlit Community Cloud: 1 GB RAM, shared CPU — sufficient for scanner workloads on small universes (<50 tickers).
- FastAPI: stateless; scale horizontally. SQLite is single-writer; use Postgres for multi-instance deployments.

## v1.0 Production Checklist

Use this before running IVSURF in a shared or production environment.

### Security

- [ ] Set `IVSURF_API_KEY` on any publicly reachable FastAPI instance
- [ ] Pass the same key to WebSocket clients via `?api_key=...`
- [ ] Store Alpaca keys and webhook URLs in secrets (Streamlit secrets, GitHub Actions secrets, or your host's env manager) — never commit them
- [ ] Use Alpaca **paper** credentials (`ALPACA_BASE_URL=https://paper-api.alpaca.markets`) until strategies are validated

### Data and storage

- [ ] Configure Alpaca for 1-min + premarket bars; yfinance fallback is delayed and limited to ~7 days of 1-min history
- [ ] For multi-instance API deployments, set `IVSURF_DATABASE_URL` to a shared PostgreSQL database
- [ ] Back up `data/ivsurf.db` (SQLite) or your Postgres instance regularly if signal history matters
- [ ] Monitor Yahoo Finance rate limits on large universes (>50 tickers)

### Trading and automation

- [ ] Keep `IVSURF_GUARDRAILS_ENABLED=true` for any automated order flow
- [ ] Set conservative `IVSURF_MAX_DAILY_LOSS_PCT`, `IVSURF_MAX_OPEN_POSITIONS`, and `IVSURF_MAX_NOTIONAL_PER_TRADE`
- [ ] Require explicit UI confirmation before submitting orders in the Opening Scanner
- [ ] Use `IVSURF_BROKER=simulated` for demos and integration tests without external API calls
- [ ] Set `min_score` conservatively on scheduled pre-market scans and webhook alerts

### Operations

- [ ] Run `pytest` (141+ tests) before deploying config changes
- [ ] Verify `/health` returns `"status": "ok"` after API deploy
- [ ] Confirm the pre-market GitHub Action schedule (13:00 UTC weekdays) matches your timezone needs
- [ ] Retrain the ML ranker after sufficient labeled signals: `python scripts/train_ml_ranker.py --min-samples 30`
- [ ] Pin Python 3.9–3.11 in production (CI-tested versions)

### Release

Tagged releases: [GitHub Releases](https://github.com/DDVHegde100/ivsurf/releases). See [CHANGELOG.md](CHANGELOG.md) for version history.
