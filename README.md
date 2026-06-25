# OpenPulse

**OpenPulse** is an opening-hours volatility scanner and spatial research platform — 3D math visualizations, ML graphs, knowledge maps, and optional paper trading. Built as an educational and research tool, not a live trading system.

Formerly **IVSURF** (Integrated Volatility Surface Research Facility). The GitHub repo remains `ivsurf`; environment variables keep the `IVSURF_*` prefix for compatibility.

![OpenPulse Terminal](scripts/23.png)

[![Launch Live Demo](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ivsurf-volatility-explorer.streamlit.app)

## Live Demo

[https://ivsurf-volatility-explorer.streamlit.app](https://ivsurf-volatility-explorer.streamlit.app)

## What It Does

OpenPulse combines opening-hours scanning, 3D spatial analytics, and classical quant finance in a Streamlit terminal:

- **3D Spatial Lab** — parametric math surfaces, ML loss landscapes, PCA feature space, knowledge graphs, correlation sphere, opening score terrain
- **Opening scanner** — ranks tickers by gap, premarket volume, opening range, and regime-adjusted scores
- **Market scanner** — ranks NASDAQ tickers by rule-based swing opportunity scores
- **Volatility surfaces** — builds and visualizes IV surfaces from Yahoo Finance options chains
- **Quant models** — GARCH, regime switching, Heston MC, VaR, Monte Carlo simulation
- **ML forecasting** — sklearn ensemble + walk-forward XGBoost ranker (TensorFlow LSTM optional)
- **Risk analytics** — VaR, stress testing, regime-aware backtesting
- **REST API** — FastAPI endpoints for scan, predict, signal history, and live opening-range websocket
- **Paper trading** — Alpaca and simulated brokers with pre-trade guardrails

**Data sources:** Yahoo Finance (default). Alpaca optional for 1-min bars and paper trading.

## Quick Start

```bash
git clone https://github.com/DDVHegde100/ivsurf.git
cd ivsurf

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
streamlit run scripts/ivsurf_retro_terminal.py --server.port 8503

# Optional: REST API
pip install -e ".[api]"
uvicorn api.main:app --reload --port 8000

# Docker (UI + API)
./scripts/compose-up.sh
```

### Optional Dependencies

Install extras via `pyproject.toml`:

```bash
pip install -e ".[dev]"        # pytest, ruff
pip install -e ".[ml]"           # TensorFlow for LSTM models
pip install -e ".[quant]"        # arch, statsmodels for clustering diagnostics
pip install -e ".[perf]"         # numba for Monte Carlo acceleration
pip install -e ".[all]"          # everything
```

## Project Structure

```
ivsurf/
├── engine/                  # Business logic (data, features, signals, backtest, execution)
├── api/                     # FastAPI routes (OpenPulse API)
├── app/                     # Streamlit UI components and themes
├── core/                    # Black-Scholes, Greeks, spatial geometry
├── visuals/plot_3d/         # 3D Plotly visualizations
├── models/                  # GARCH, regime switching, Heston, jump diffusion
├── ml/                      # Volatility forecasting, neural networks
├── scripts/
│   └── ivsurf_retro_terminal.py   # Main Streamlit app
└── tests/                   # pytest suite
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest                          # unit tests (excludes integration by default)
pytest -m integration           # live market data tests (requires network)
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud, Docker Compose, FastAPI, and Alpaca setup.

## Known Limitations

- Opening scanner uses **heuristic scoring** with optional ML re-ranking when a trained model is present
- Yahoo Finance data is delayed and may break without notice; Alpaca recommended for intraday bars
- Live order submission requires explicit user confirmation; guardrails are enabled by default
- Not investment advice — research and educational use only

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License — see [LICENSE](LICENSE).

## Disclaimer

This software is for **educational and research purposes only**. Not investment advice. All trading involves substantial risk of loss.

---

**Dhruv Hegde** — Quantitative Developer & Trading Systems Engineer
