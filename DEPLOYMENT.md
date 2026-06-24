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

Copy `.env.example` to `.env` for local development.

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
