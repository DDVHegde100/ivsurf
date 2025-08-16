# Volatility Surface Explorer

A tool for modeling and visualizing implied volatility (IV) surfaces across strikes and expirations.

## Features
- Fetches real-time options chain data (Yahoo Finance API)
- Calculates implied volatility using Black-Scholes inversion
- Builds 3D volatility surfaces with interpolation
- Interactive Streamlit dashboard for visualization
- Heatmaps of Greeks (Delta, Gamma, Vega)

## Getting Started
```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Repo Structure
- `core/` → math & model logic (BSM, Greeks, interpolation)
- `visuals/` → plotting functions (3D, heatmaps)
- `dashboard/` → Streamlit app
- `data/` → cache/data storage
- `utils/` → scraping & helpers
- `notebooks/` → experimentation

