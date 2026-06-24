"""Rule-based opening volatility scanner."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd
import yfinance as yf

from engine.data.alpaca import IntradayDataFetcher
from engine.features.daily import compute_daily_features
from engine.features.intraday import compute_intraday_features
from engine.signals.regime_filter import RegimeFilter


def score_opening_features(features: dict[str, float], regime_multiplier: float = 1.0) -> float:
    """
    Heuristic opening opportunity score (0–100).

    Weights gap, premarket activity, opening range expansion, and relative volume.
    """
    gap = abs(features.get("gap_pct", 0.0))
    gap_score = min(gap * 8, 30) if gap >= 1.0 else gap * 5

    pm_ratio = features.get("premarket_volume_ratio", 0.0)
    pm_score = min(pm_ratio * 25, 25)

    or_range = features.get("or_15m_range_pct", features.get("or_5m_range_pct", 0.0))
    or_score = min(or_range * 4, 25)

    rel_vol = features.get("relative_volume_open", 0.0)
    vol_score = min(max(rel_vol - 1, 0) * 15, 20)

    raw = gap_score + pm_score + or_score + vol_score
    return float(min(100, raw * regime_multiplier))


def scan_ticker(
    ticker: str,
    fetcher: IntradayDataFetcher | None = None,
    regime_filter: RegimeFilter | None = None,
) -> dict[str, Any] | None:
    """Score a single ticker for opening volatility opportunity."""
    fetcher = fetcher or IntradayDataFetcher()
    try:
        daily = yf.Ticker(ticker).history(period="60d", interval="1d")
        if daily.empty or len(daily) < 20:
            return None

        prior_close = float(daily["Close"].iloc[-2])
        avg_volume = float(daily["Volume"].tail(20).mean())
        daily_features = compute_daily_features(daily)

        garch_forecast = None
        regime_multiplier = 1.0
        regime_label = "unknown"
        if regime_filter is not None:
            regime_info = regime_filter.evaluate(daily["Close"].pct_change().dropna())
            regime_multiplier = regime_info["score_multiplier"]
            regime_label = regime_info["regime_label"]
            garch_forecast = regime_info.get("garch_forecast")

        bars = fetcher.get_bars(ticker, timeframe="1Min")
        if bars.empty:
            return None

        intraday = compute_intraday_features(
            bars,
            prior_close=prior_close,
            avg_daily_volume=avg_volume,
            garch_vol_forecast=garch_forecast,
        )

        score = score_opening_features(intraday, regime_multiplier)

        direction = "up" if intraday["gap_pct"] >= 0 else "down"
        return {
            "ticker": ticker.upper(),
            "opening_score": score,
            "direction": direction,
            "price": daily_features["current_price"],
            "gap_pct": intraday["gap_pct"],
            "premarket_volume_ratio": intraday["premarket_volume_ratio"],
            "or_15m_range_pct": intraday.get("or_15m_range_pct", 0.0),
            "relative_volume_open": intraday["relative_volume_open"],
            "volatility": daily_features["volatility"],
            "regime_label": regime_label,
            "regime_multiplier": regime_multiplier,
            **intraday,
        }
    except Exception:
        return None


def scan_universe(
    tickers: list[str],
    max_workers: int = 4,
    regime_filter: RegimeFilter | None = None,
    min_score: float = 20.0,
) -> pd.DataFrame:
    """Scan tickers in parallel and return ranked opportunities."""
    fetcher = IntradayDataFetcher()
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(scan_ticker, t, fetcher, regime_filter): t for t in tickers
        }
        for future in as_completed(futures):
            try:
                row = future.result(timeout=30)
                if row and row.get("opening_score", 0) >= min_score:
                    results.append(row)
            except Exception:
                continue

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results).sort_values("opening_score", ascending=False)
    return df.reset_index(drop=True)
