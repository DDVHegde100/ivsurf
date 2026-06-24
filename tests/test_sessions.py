"""Tests for US equity session utilities."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from engine.data.sessions import (
    ET,
    aggregate_bars,
    filter_session,
    is_trading_day,
    opening_window,
    session_bounds,
)

ET_TZ = ZoneInfo("America/New_York")


def _make_intraday_index(start_hour: int, n: int = 60) -> pd.DatetimeIndex:
    base = datetime(2025, 6, 2, start_hour, 0, tzinfo=ET_TZ)
    return pd.date_range(base, periods=n, freq="1min", tz=ET_TZ)


class TestSessions:
    def test_is_trading_day(self):
        assert is_trading_day(date(2025, 6, 2))  # Monday
        assert not is_trading_day(date(2025, 6, 1))  # Sunday

    def test_session_bounds_rth(self):
        start, end = session_bounds(date(2025, 6, 2), "rth")
        assert start.hour == 9 and start.minute == 30
        assert end.hour == 16 and end.minute == 0

    def test_filter_premarket(self):
        idx = _make_intraday_index(4, n=330)
        df = pd.DataFrame({"Open": 1, "High": 1, "Low": 1, "Close": 1, "Volume": 100}, index=idx)
        pm = filter_session(df, "premarket")
        assert len(pm) > 0
        assert all(t.hour < 9 or (t.hour == 9 and t.minute < 30) for t in pm.index.time)

    def test_opening_window(self):
        idx = pd.date_range(datetime(2025, 6, 2, 9, 30, tzinfo=ET_TZ), periods=60, freq="1min")
        df = pd.DataFrame({"Open": 1, "High": 1, "Low": 1, "Close": 1, "Volume": 100}, index=idx)
        window = opening_window(df, date(2025, 6, 2), minutes=15)
        assert len(window) == 15

    def test_aggregate_bars(self):
        idx = pd.date_range(datetime(2025, 6, 2, 9, 30, tzinfo=ET_TZ), periods=10, freq="1min")
        df = pd.DataFrame(
            {"Open": range(10), "High": range(10), "Low": range(10), "Close": range(10), "Volume": 100},
            index=idx,
        )
        agg = aggregate_bars(df, "5min")
        assert len(agg) == 2
