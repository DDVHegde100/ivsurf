"""Signal outcome labeling for ML training and backtesting."""

from __future__ import annotations

from datetime import timedelta
from typing import Literal

import numpy as np
import pandas as pd

from engine.data.sessions import session_bounds, to_eastern

Horizon = Literal["1h", "1d", "3d"]
Label = Literal["big_mover_up", "big_mover_down", "flat", "swing_3d"]


def _first_hour_window(intraday_bars: pd.DataFrame, trading_date) -> pd.DataFrame:
    open_dt, _ = session_bounds(trading_date, "rth")
    end_dt = open_dt + timedelta(hours=1)
    idx = intraday_bars.index.tz_convert("America/New_York") if intraday_bars.index.tz else intraday_bars.index
    return intraday_bars.loc[(idx >= pd.Timestamp(open_dt)) & (idx < pd.Timestamp(end_dt))]


def compute_horizon_return(
    intraday_bars: pd.DataFrame,
    daily_bars: pd.DataFrame,
    entry_price: float,
    horizon: Horizon,
    signal_date: pd.Timestamp,
) -> float | None:
    """Realized return from entry for a given horizon."""
    if entry_price <= 0:
        return None

    signal_date = to_eastern(signal_date)
    trading_date = signal_date.date()

    if horizon == "1h":
        window = _first_hour_window(intraday_bars, trading_date)
        if window.empty:
            return None
        exit_price = float(window["Close"].iloc[-1])
        return (exit_price / entry_price) - 1

    if daily_bars.empty:
        return None

    daily = daily_bars.copy()
    if daily.index.tz is None:
        daily.index = daily.index.tz_localize("America/New_York")
    else:
        daily.index = daily.index.tz_convert("America/New_York")

    future = daily.loc[daily.index > signal_date.normalize()]
    if future.empty:
        return None

    days = 1 if horizon == "1d" else 3
    if len(future) < days:
        return None

    exit_price = float(future["Close"].iloc[days - 1])
    return (exit_price / entry_price) - 1


def label_return(ret: float, threshold: float = 0.03) -> Label:
    """Classify a realized return into outcome labels."""
    if ret >= threshold:
        return "big_mover_up"
    if ret <= -threshold:
        return "big_mover_down"
    return "flat"


def label_signal_outcomes(
    intraday_bars: pd.DataFrame,
    daily_bars: pd.DataFrame,
    entry_price: float,
    signal_date: pd.Timestamp,
    up_threshold: float = 0.03,
    swing_threshold: float = 0.05,
) -> dict:
    """
    Compute realized outcomes and binary labels at 1h, 1d, and 3d horizons.
    """
    outcomes: dict = {}
    for horizon in ("1h", "1d", "3d"):
        ret = compute_horizon_return(intraday_bars, daily_bars, entry_price, horizon, signal_date)
        if ret is None:
            outcomes[horizon] = {"return": None, "label": None}
            continue

        lbl = label_return(ret, threshold=up_threshold)
        outcomes[horizon] = {"return": float(ret), "label": lbl}

    ret_3d = outcomes.get("3d", {}).get("return")
    swing_label = None
    if ret_3d is not None and abs(ret_3d) >= swing_threshold:
        swing_label = "swing_3d"

    return {
        "entry_price": entry_price,
        "signal_date": str(signal_date),
        "outcomes": outcomes,
        "swing_3d": swing_label,
        "big_mover_up": outcomes.get("1h", {}).get("label") == "big_mover_up",
        "big_mover_down": outcomes.get("1h", {}).get("label") == "big_mover_down",
    }


def build_labeled_dataset(rows: list[dict]) -> pd.DataFrame:
    """Flatten labeled signal rows into a training DataFrame."""
    records = []
    for row in rows:
        features = row.get("features", {})
        labels = row.get("labels", {})
        record = {**features}
        record["ticker"] = row.get("ticker")
        record["signal_date"] = row.get("signal_date")
        for key, val in labels.items():
            record[f"label_{key}"] = val
        records.append(record)
    return pd.DataFrame(records)
