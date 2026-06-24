"""Opening range snapshot feed for live monitoring."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from engine.data.alpaca import IntradayDataFetcher
from engine.data.sessions import opening_window, session_bounds, to_eastern
from engine.features.intraday import compute_opening_range_features, compute_relative_volume_at_open

ET = ZoneInfo("America/New_York")
DEFAULT_WINDOWS = (5, 15, 30)
MAX_TICKERS = 50


def build_opening_range_snapshot(
    ticker: str,
    intraday_bars: pd.DataFrame,
    *,
    prior_close: float,
    avg_daily_volume: float,
    trading_date: date | None = None,
    windows: tuple[int, ...] = DEFAULT_WINDOWS,
) -> dict[str, Any] | None:
    """Build a structured opening-range snapshot from intraday bars."""
    if intraday_bars.empty:
        return None

    if trading_date is None:
        trading_date = to_eastern(intraday_bars.index[-1]).date()

    open_dt, _ = session_bounds(trading_date, "rth")
    rth = intraday_bars.loc[intraday_bars.index >= pd.Timestamp(open_dt)]
    if rth.empty:
        return None

    day_open = float(rth["Open"].iloc[0])
    last_price = float(rth["Close"].iloc[-1])
    if day_open <= 0:
        return None

    or_features = compute_opening_range_features(intraday_bars, trading_date, windows=windows)
    avg_minute_vol = avg_daily_volume / 390 if avg_daily_volume > 0 else 0.0
    rel_vol = compute_relative_volume_at_open(
        intraday_bars,
        avg_minute_vol,
        minutes=30,
        trading_date=trading_date,
    )

    windows_out: dict[str, dict[str, float]] = {}
    for minutes in windows:
        window = opening_window(intraday_bars, trading_date, minutes=minutes)
        if window.empty:
            windows_out[f"{minutes}m"] = {
                "high": day_open,
                "low": day_open,
                "range_pct": 0.0,
                "volume": 0.0,
                "complete": False,
            }
            continue

        high = float(window["High"].max())
        low = float(window["Low"].min())
        now = to_eastern(intraday_bars.index[-1])
        complete = now >= open_dt + pd.Timedelta(minutes=minutes)
        windows_out[f"{minutes}m"] = {
            "high": high,
            "low": low,
            "range_pct": float(or_features.get(f"or_{minutes}m_range_pct", 0.0)),
            "volume": float(or_features.get(f"or_{minutes}m_volume", 0.0)),
            "complete": complete,
        }

    gap_pct = float((day_open / prior_close - 1) * 100) if prior_close > 0 else 0.0
    breakout = "inside"
    primary = windows_out.get("15m") or next(iter(windows_out.values()))
    if last_price > primary["high"]:
        breakout = "above"
    elif last_price < primary["low"]:
        breakout = "below"

    return {
        "ticker": ticker.upper(),
        "trading_date": trading_date.isoformat(),
        "day_open": day_open,
        "last_price": last_price,
        "prior_close": prior_close,
        "gap_pct": gap_pct,
        "relative_volume_open": rel_vol,
        "breakout": breakout,
        "windows": windows_out,
        "updated_at": datetime.now(tz=ET).isoformat(),
    }


class OpeningRangeFeed:
    """Poll intraday bars and emit opening-range snapshots."""

    def __init__(
        self,
        fetcher: IntradayDataFetcher | None = None,
        *,
        cache_duration_minutes: int = 1,
    ):
        self._fetcher = fetcher or IntradayDataFetcher(cache_duration_minutes=cache_duration_minutes)
        self._daily_cache: dict[str, tuple[float, float]] = {}

    def _daily_stats(self, ticker: str) -> tuple[float, float] | None:
        cached = self._daily_cache.get(ticker.upper())
        if cached is not None:
            return cached

        daily = yf.Ticker(ticker).history(period="60d", interval="1d")
        if daily.empty or len(daily) < 2:
            return None

        prior_close = float(daily["Close"].iloc[-2])
        avg_volume = float(daily["Volume"].tail(20).mean())
        self._daily_cache[ticker.upper()] = (prior_close, avg_volume)
        return prior_close, avg_volume

    def snapshot(self, ticker: str) -> dict[str, Any] | None:
        stats = self._daily_stats(ticker)
        if stats is None:
            return None

        prior_close, avg_volume = stats
        bars = self._fetcher.get_bars(ticker, timeframe="1Min")
        return build_opening_range_snapshot(
            ticker,
            bars,
            prior_close=prior_close,
            avg_daily_volume=avg_volume,
        )

    def snapshots(self, tickers: list[str]) -> list[dict[str, Any]]:
        unique = []
        seen: set[str] = set()
        for ticker in tickers:
            symbol = ticker.strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            unique.append(symbol)
            if len(unique) >= MAX_TICKERS:
                break

        results: list[dict[str, Any]] = []
        for symbol in unique:
            try:
                row = self.snapshot(symbol)
                if row is not None:
                    results.append(row)
            except Exception:
                continue
        return results
