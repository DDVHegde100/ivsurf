# Roadmap

**OpenPulse** (formerly IVSURF) is a focused opening-hours volatility scanner with 3D spatial analytics, walk-forward validation, and optional paper trading.

## Completed (v0.3)

- [x] Engine extraction from Streamlit monolith
- [x] Intraday data layer (Alpaca + yfinance fallback)
- [x] Opening volatility scanner with regime filter
- [x] Walk-forward ML ranker and outcome labeling
- [x] FastAPI layer (`/scan`, `/predict`, `/signals/history`)
- [x] Opening Scanner + Signal Performance UI tabs
- [x] Retro/Modern theme toggle
- [x] Alpaca paper trader adapter (dry-run + live)
- [x] CI test suite (57+ unit tests)

## Near Term (v0.4)

- [x] Wire paper trader into Opening Scanner tab (explicit user confirmation)
- [x] Scheduled pre-market scan (cron / GitHub Action)
- [x] Signal history dashboard with equity curve
- [x] Authentication on FastAPI routes
- [x] Postgres adapter for multi-user deployments

## Medium Term (v0.5)

- [x] Train ML ranker on accumulated labeled signals in SQLite
- [x] Options-aware opening plays (straddles/strangles on high OR expansion)
- [x] Alert webhooks (Slack, Discord) for scores above threshold
- [x] Expand universe management (watchlists, sector filters)

## Long Term

- [x] Live trading guardrails (max daily loss, position limits)
- [x] Broker abstraction beyond Alpaca
- [x] Real-time websocket feed for opening range updates

## v1.0 (2026-06-24)

- [x] Version bump and changelog
- [x] Production deployment checklist
- [x] GitHub release tag `v1.0.0`

## Post v1.0

- [x] NYSE holiday calendar for session and pre-market scan scheduling
- [x] Streamlit live opening range monitor (Opening Scanner tab)
- [x] 3D Spatial Lab (math surfaces, ML graphs, knowledge maps)
- [x] Docker Compose one-command deploy (Streamlit + API)
- [x] OpenPulse product rebrand

## v1.2 — Advanced 3D Analytics

- [x] Animated parametric surfaces
- [x] 3D neural network architecture graph
- [x] Portfolio risk ellipsoid & IV smile surface
- [x] Fourier spectral, price ribbon, Monte Carlo path cloud
- [x] HTML export for 3D Plotly figures

## v1.3 — Vercel & Quant 3D

- [x] Vercel serverless OpenPulse API deployment
- [x] Heston, Greeks, regime graph, weight heatmap 3D
- [x] Vector field, correlation tubes, opening range 3D
- [x] Spatial JSON API (`/spatial/*`)

## Non-Goals

- Replacing Bloomberg or institutional OMS systems
- Unattended live trading without explicit user configuration
- Crypto or forex (US equities focus)

## How to Influence the Roadmap

Open a GitHub issue with the `enhancement` label. PRs that implement roadmap items with tests are welcome.
