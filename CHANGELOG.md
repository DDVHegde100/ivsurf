# Changelog

All notable changes to OpenPulse (formerly IVSURF) are documented here.

## [1.1.0] - 2026-06-24

### Added

- 3D Spatial Lab — math surfaces, ML graphs, knowledge maps, correlation sphere
- Docker Compose one-command deploy (Streamlit UI + FastAPI + optional Postgres)

### Changed

- Product rebrand from IVSURF to **OpenPulse** (UI, API, docs)
- `IVSURF_*` environment variables retained for backward compatibility

## [1.0.0] - 2026-06-24

First stable release of the opening-hours volatility scanner platform.

### Added

- Opening volatility scanner with regime filter, ML re-ranking, and options play suggestions
- FastAPI layer: `/scan`, `/predict`, `/signals/history`, `/universes`, `/ws/opening-range`
- Streamlit UI: Opening Scanner, Signal Performance dashboard, retro/modern themes
- Alpaca intraday data with yfinance fallback; paper and simulated broker execution
- Trading guardrails (daily loss, position limits, notional caps)
- Pluggable broker adapters (`alpaca`, `simulated`)
- SQLite and PostgreSQL signal storage backends
- ML ranker training pipeline from labeled signal history
- Slack/Discord webhook alerts for high-score scan hits
- Watchlist and sector universe management
- Scheduled pre-market scan (GitHub Action + CLI)
- Real-time opening range websocket feed
- Optional API key authentication on REST and WebSocket routes

### Testing

- 141+ unit tests; CI on Python 3.9 and 3.11

[1.1.0]: https://github.com/DDVHegde100/ivsurf/releases/tag/v1.1.0
[1.0.0]: https://github.com/DDVHegde100/ivsurf/releases/tag/v1.0.0
