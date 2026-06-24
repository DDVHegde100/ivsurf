"""
Intraday bar fetcher via Alpaca Markets API with yfinance fallback.

Requires ALPACA_API_KEY and ALPACA_SECRET_KEY env vars for Alpaca.
Falls back to yfinance 1-min bars when credentials are absent.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from engine.data.cache import TTLCache

ET = ZoneInfo("America/New_York")
BarTimeframe = Literal["1Min", "5Min", "15Min", "1Hour", "1Day"]

_ALPACA_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


class IntradayDataFetcher:
    """Fetch 1-min and premarket bars from Alpaca or yfinance."""

    def __init__(self, cache_duration_minutes: int = 5):
        self._cache = TTLCache[pd.DataFrame](timedelta(minutes=cache_duration_minutes))
        self._api_key = os.environ.get("ALPACA_API_KEY", "").strip()
        self._secret_key = os.environ.get("ALPACA_SECRET_KEY", "").strip()
        self._base_url = os.environ.get(
            "ALPACA_BASE_URL", "https://paper-api.alpaca.markets"
        ).rstrip("/")

    @property
    def alpaca_configured(self) -> bool:
        return bool(self._api_key and self._secret_key)

    def get_bars(
        self,
        ticker: str,
        timeframe: BarTimeframe = "1Min",
        start: datetime | None = None,
        end: datetime | None = None,
        include_premarket: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV bars for a ticker.

        Returns DataFrame indexed by US/Eastern timestamp with columns:
        Open, High, Low, Close, Volume.
        """
        cache_key = f"{ticker}_{timeframe}_{start}_{end}_{include_premarket}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached.copy()

        if end is None:
            end = datetime.now(tz=ET)
        if start is None:
            start = end - timedelta(days=5)

        if self.alpaca_configured:
            try:
                df = self._fetch_alpaca(ticker, timeframe, start, end, include_premarket)
                if not df.empty:
                    self._cache.set(cache_key, df.copy())
                    return df
            except Exception:
                pass

        df = self._fetch_yfinance(ticker, timeframe, start, end)
        if not df.empty:
            self._cache.set(cache_key, df.copy())
        return df

    def _fetch_alpaca(
        self,
        ticker: str,
        timeframe: BarTimeframe,
        start: datetime,
        end: datetime,
        include_premarket: bool,
    ) -> pd.DataFrame:
        import urllib.parse
        import urllib.request
        import json

        params = urllib.parse.urlencode(
            {
                "symbols": ticker.upper(),
                "timeframe": timeframe,
                "start": start.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 10000,
                "adjustment": "raw",
                "feed": "iex",
            }
        )
        url = f"{self._base_url}/v2/stocks/bars?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._secret_key,
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())

        bars = payload.get("bars", {}).get(ticker.upper(), [])
        if not bars:
            return pd.DataFrame(columns=_ALPACA_COLUMNS)

        rows = []
        for bar in bars:
            ts = pd.Timestamp(bar["t"]).tz_convert(ET)
            rows.append(
                {
                    "timestamp": ts,
                    "Open": bar["o"],
                    "High": bar["h"],
                    "Low": bar["l"],
                    "Close": bar["c"],
                    "Volume": bar["v"],
                }
            )

        df = pd.DataFrame(rows).set_index("timestamp").sort_index()
        if not include_premarket:
            from engine.data.sessions import filter_regular_session

            df = filter_regular_session(df)
        return df

    @staticmethod
    def _filter_regular_session(df: pd.DataFrame) -> pd.DataFrame:
        from engine.data.sessions import filter_regular_session

        return filter_regular_session(df)

    def _fetch_yfinance(
        self,
        ticker: str,
        timeframe: BarTimeframe,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        interval_map = {
            "1Min": "1m",
            "5Min": "5m",
            "15Min": "15m",
            "1Hour": "1h",
            "1Day": "1d",
        }
        interval = interval_map.get(timeframe, "1m")
        # yfinance 1m data limited to ~7 days
        period = "7d" if interval in ("1m", "5m") else "60d"

        hist = yf.Ticker(ticker).history(period=period, interval=interval, prepost=True)
        if hist.empty:
            return pd.DataFrame(columns=_ALPACA_COLUMNS)

        df = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
        if df.index.tz is None:
            df.index = df.index.tz_localize(ET)
        else:
            df.index = df.index.tz_convert(ET)

        start_ts = pd.Timestamp(start).tz_convert(ET) if start.tzinfo else pd.Timestamp(start, tz=ET)
        end_ts = pd.Timestamp(end).tz_convert(ET) if end.tzinfo else pd.Timestamp(end, tz=ET)
        return df.loc[(df.index >= start_ts) & (df.index <= end_ts)]
