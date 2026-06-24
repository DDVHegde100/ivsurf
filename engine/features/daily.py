"""Daily-bar technical features for swing scanning."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_rsi(close: pd.Series, window: int = 14) -> float:
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=min(window, len(close))).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=min(window, len(close))).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    if len(rsi) == 0 or loss.iloc[-1] == 0:
        return 50.0
    return float(rsi.iloc[-1])


def compute_macd(close: pd.Series) -> tuple[float, float, float]:
    ema_12 = close.ewm(span=min(12, len(close))).mean().iloc[-1]
    ema_26 = close.ewm(span=min(26, len(close))).mean().iloc[-1]
    macd = ema_12 - ema_26
    macd_signal = close.ewm(span=min(9, len(close))).mean().iloc[-1]
    macd_histogram = macd - macd_signal
    return float(macd), float(macd_signal), float(macd_histogram)


def compute_bollinger_position(close: pd.Series, current_price: float, window: int = 20) -> float:
    period = min(window, len(close))
    bb_mean = close.rolling(period).mean().iloc[-1]
    bb_std = close.rolling(period).std().iloc[-1]
    bb_upper = bb_mean + (bb_std * 2)
    bb_lower = bb_mean - (bb_std * 2)
    if bb_upper == bb_lower:
        return 0.5
    return float((current_price - bb_lower) / (bb_upper - bb_lower))


def compute_volatility(hist_long: pd.DataFrame, default: float = 0.25) -> float:
    if len(hist_long) <= 20:
        return default
    returns = hist_long["Close"].pct_change().dropna()
    return float(returns.std() * np.sqrt(252))


def compute_volume_metrics(hist: pd.DataFrame) -> tuple[float, float, float]:
    avg_volume = hist["Volume"].mean()
    current_volume = hist["Volume"].iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    vol_3d = hist["Volume"].tail(3).mean()
    vol_10d = hist["Volume"].tail(10).mean()
    volume_trend = (vol_3d / vol_10d) if vol_10d > 0 else 1.0
    return float(current_volume), float(volume_ratio), float(volume_trend)


def compute_momentum(hist: pd.DataFrame, current_price: float, price_change_pct: float) -> tuple[float, float, float]:
    momentum_1d = price_change_pct
    momentum_3d = (
        (current_price - hist["Close"].iloc[-4]) / hist["Close"].iloc[-4] * 100 if len(hist) > 3 else 0.0
    )
    momentum_5d = (
        (current_price - hist["Close"].iloc[-6]) / hist["Close"].iloc[-6] * 100 if len(hist) > 5 else 0.0
    )
    return float(momentum_1d), float(momentum_3d), float(momentum_5d)


def compute_moving_averages(hist: pd.DataFrame) -> tuple[float, float]:
    sma_5 = hist["Close"].rolling(window=min(5, len(hist))).mean().iloc[-1]
    sma_20 = hist["Close"].rolling(window=min(20, len(hist))).mean().iloc[-1]
    return float(sma_5), float(sma_20)


def compute_daily_features(hist: pd.DataFrame, hist_long: pd.DataFrame | None = None) -> dict:
    """Compute all daily technical features used by the market scanner."""
    current_price = float(hist["Close"].iloc[-1])
    prev_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price else 0.0

    hist_long = hist_long if hist_long is not None else hist
    volatility = compute_volatility(hist_long)
    current_volume, volume_ratio, volume_trend = compute_volume_metrics(hist)
    sma_5, sma_20 = compute_moving_averages(hist)
    _, _, macd_histogram = compute_macd(hist["Close"])
    rsi = compute_rsi(hist["Close"])
    bb_position = compute_bollinger_position(hist["Close"], current_price)
    momentum_1d, momentum_3d, momentum_5d = compute_momentum(hist, current_price, price_change_pct)

    return {
        "current_price": current_price,
        "price_change": price_change,
        "price_change_pct": price_change_pct,
        "volatility": volatility,
        "current_volume": current_volume,
        "volume_ratio": volume_ratio,
        "volume_trend": volume_trend,
        "sma_5": sma_5,
        "sma_20": sma_20,
        "rsi": rsi,
        "macd_histogram": macd_histogram,
        "bb_position": bb_position,
        "momentum_1d": momentum_1d,
        "momentum_3d": momentum_3d,
        "momentum_5d": momentum_5d,
    }
