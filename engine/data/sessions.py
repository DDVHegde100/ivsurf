"""
US equity session utilities — premarket, RTH, and opening-window boundaries.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

import pandas as pd

ET = ZoneInfo("America/New_York")

PREMARKET_OPEN = time(4, 0)
RTH_OPEN = time(9, 30)
RTH_CLOSE = time(16, 0)
AFTERHOURS_CLOSE = time(20, 0)

SessionType = Literal["premarket", "rth", "afterhours", "all"]


def to_eastern(ts: datetime | pd.Timestamp) -> pd.Timestamp:
    """Normalize a timestamp to US/Eastern."""
    t = pd.Timestamp(ts)
    if t.tz is None:
        return t.tz_localize(ET)
    return t.tz_convert(ET)


def is_trading_day(d: date) -> bool:
    """Weekday check excluding NYSE market holidays."""
    if d.weekday() >= 5:
        return False
    from engine.data.holidays import is_market_holiday

    return not is_market_holiday(d)


def session_bounds(trading_date: date, session: SessionType = "all") -> tuple[datetime, datetime]:
    """Return (start, end) datetimes in US/Eastern for a session on a given date."""
    if session == "premarket":
        start = datetime.combine(trading_date, PREMARKET_OPEN, tzinfo=ET)
        end = datetime.combine(trading_date, RTH_OPEN, tzinfo=ET)
    elif session == "rth":
        start = datetime.combine(trading_date, RTH_OPEN, tzinfo=ET)
        end = datetime.combine(trading_date, RTH_CLOSE, tzinfo=ET)
    elif session == "afterhours":
        start = datetime.combine(trading_date, RTH_CLOSE, tzinfo=ET)
        end = datetime.combine(trading_date, AFTERHOURS_CLOSE, tzinfo=ET)
    else:
        start = datetime.combine(trading_date, PREMARKET_OPEN, tzinfo=ET)
        end = datetime.combine(trading_date, AFTERHOURS_CLOSE, tzinfo=ET)
    return start, end


def filter_session(df: pd.DataFrame, session: SessionType = "rth") -> pd.DataFrame:
    """Filter intraday bars to a specific session type."""
    if df.empty:
        return df

    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize(ET)
    else:
        idx = idx.tz_convert(ET)

    times = idx.time
    if session == "premarket":
        mask = (times >= PREMARKET_OPEN) & (times < RTH_OPEN)
    elif session == "rth":
        mask = (times >= RTH_OPEN) & (times < RTH_CLOSE)
    elif session == "afterhours":
        mask = (times >= RTH_CLOSE) & (times < AFTERHOURS_CLOSE)
    else:
        return df

    return df.loc[mask]


filter_regular_session = lambda df: filter_session(df, "rth")


def opening_window(
    df: pd.DataFrame,
    trading_date: date | None = None,
    minutes: int = 30,
) -> pd.DataFrame:
    """Return bars from market open through open + N minutes."""
    if df.empty:
        return df

    if trading_date is None:
        trading_date = to_eastern(df.index[-1]).date()

    open_dt, _ = session_bounds(trading_date, "rth")
    end_dt = open_dt + timedelta(minutes=minutes)
    idx = df.index.tz_convert(ET) if df.index.tz else df.index.tz_localize(ET)
    return df.loc[(idx >= open_dt) & (idx < end_dt)]


def aggregate_bars(df: pd.DataFrame, rule: str = "5min") -> pd.DataFrame:
    """Resample 1-min bars to a coarser timeframe."""
    if df.empty:
        return df
    ohlcv = df.resample(rule).agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    )
    return ohlcv.dropna(subset=["Open"])
