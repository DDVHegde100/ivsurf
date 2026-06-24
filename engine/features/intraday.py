"""Intraday feature engineering for opening-hours scanning."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from engine.data.sessions import opening_window, session_bounds, to_eastern


def compute_gap_pct(prior_close: float, open_price: float) -> float:
    if prior_close <= 0:
        return 0.0
    return float((open_price / prior_close - 1) * 100)


def compute_premarket_features(premarket_bars: pd.DataFrame, avg_daily_volume: float) -> dict:
    """Features from premarket session bars."""
    if premarket_bars.empty:
        return {
            "premarket_volume": 0.0,
            "premarket_volume_ratio": 0.0,
            "premarket_range_pct": 0.0,
            "premarket_direction_pct": 0.0,
        }

    pm_vol = float(premarket_bars["Volume"].sum())
    pm_open = float(premarket_bars["Open"].iloc[0])
    pm_close = float(premarket_bars["Close"].iloc[-1])
    pm_high = float(premarket_bars["High"].max())
    pm_low = float(premarket_bars["Low"].min())

    vol_ratio = pm_vol / avg_daily_volume if avg_daily_volume > 0 else 0.0
    range_pct = (pm_high - pm_low) / pm_open * 100 if pm_open > 0 else 0.0
    direction_pct = (pm_close / pm_open - 1) * 100 if pm_open > 0 else 0.0

    return {
        "premarket_volume": pm_vol,
        "premarket_volume_ratio": float(vol_ratio),
        "premarket_range_pct": float(range_pct),
        "premarket_direction_pct": float(direction_pct),
    }


def compute_opening_range_features(
    intraday_bars: pd.DataFrame,
    trading_date: date | None = None,
    windows: tuple[int, ...] = (5, 15, 30),
) -> dict:
    """Opening range breakout features for multiple window sizes."""
    features: dict = {}
    if intraday_bars.empty:
        for w in windows:
            features[f"or_{w}m_range_pct"] = 0.0
            features[f"or_{w}m_volume"] = 0.0
        return features

    if trading_date is None:
        trading_date = to_eastern(intraday_bars.index[-1]).date()

    open_dt, _ = session_bounds(trading_date, "rth")
    day_open = None
    rth = intraday_bars.loc[intraday_bars.index >= pd.Timestamp(open_dt)]
    if not rth.empty:
        day_open = float(rth["Open"].iloc[0])

    for w in windows:
        window = opening_window(intraday_bars, trading_date, minutes=w)
        if window.empty or day_open is None or day_open <= 0:
            features[f"or_{w}m_range_pct"] = 0.0
            features[f"or_{w}m_volume"] = 0.0
            continue

        high = float(window["High"].max())
        low = float(window["Low"].min())
        features[f"or_{w}m_range_pct"] = float((high - low) / day_open * 100)
        features[f"or_{w}m_volume"] = float(window["Volume"].sum())

    return features


def compute_relative_volume_at_open(
    intraday_bars: pd.DataFrame,
    avg_minute_volume: float,
    minutes: int = 30,
    trading_date: date | None = None,
) -> float:
    """Volume in first N minutes vs historical average minute volume."""
    window = opening_window(intraday_bars, trading_date, minutes=minutes)
    if window.empty or avg_minute_volume <= 0:
        return 0.0
    expected = avg_minute_volume * minutes
    return float(window["Volume"].sum() / expected)


def compute_vwap_deviation(bars: pd.DataFrame) -> float:
    """Current price deviation from session VWAP (%)."""
    if bars.empty:
        return 0.0
    typical = (bars["High"] + bars["Low"] + bars["Close"]) / 3
    vol = bars["Volume"].replace(0, np.nan)
    vwap = (typical * vol).sum() / vol.sum()
    last = float(bars["Close"].iloc[-1])
    if pd.isna(vwap) or vwap <= 0:
        return 0.0
    return float((last / vwap - 1) * 100)


def compute_intraday_features(
    intraday_bars: pd.DataFrame,
    prior_close: float,
    avg_daily_volume: float,
    garch_vol_forecast: float | None = None,
    trading_date: date | None = None,
) -> dict:
    """Full intraday feature vector for opening scanner."""
    from engine.data.sessions import filter_session

    if trading_date is None and not intraday_bars.empty:
        trading_date = to_eastern(intraday_bars.index[-1]).date()

    premarket = filter_session(intraday_bars, "premarket")
    pm = compute_premarket_features(premarket, avg_daily_volume)
    or_features = compute_opening_range_features(intraday_bars, trading_date)

    open_dt, _ = session_bounds(trading_date, "rth") if trading_date else (None, None)
    day_open = prior_close
    if open_dt is not None:
        rth = intraday_bars.loc[intraday_bars.index >= pd.Timestamp(open_dt)]
        if not rth.empty:
            day_open = float(rth["Open"].iloc[0])

    gap_pct = compute_gap_pct(prior_close, day_open)
    avg_minute_vol = avg_daily_volume / 390 if avg_daily_volume > 0 else 0.0
    rel_vol = compute_relative_volume_at_open(intraday_bars, avg_minute_vol, trading_date=trading_date)
    vwap_dev = compute_vwap_deviation(filter_session(intraday_bars, "rth"))

    realized_range = 0.0
    rth_bars = filter_session(intraday_bars, "rth")
    if not rth_bars.empty and day_open > 0:
        realized_range = float((rth_bars["High"].max() - rth_bars["Low"].min()) / day_open * 100)

    vol_expansion = 0.0
    if garch_vol_forecast and garch_vol_forecast > 0 and realized_range > 0:
        vol_expansion = float(realized_range / (garch_vol_forecast * 100))

    return {
        "gap_pct": gap_pct,
        "day_open": day_open,
        "relative_volume_open": rel_vol,
        "vwap_deviation_pct": vwap_dev,
        "realized_intraday_range_pct": realized_range,
        "vol_expansion_vs_garch": vol_expansion,
        **pm,
        **or_features,
    }
