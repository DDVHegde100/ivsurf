"""Tests for intraday feature engineering."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from engine.features.intraday import (
    compute_gap_pct,
    compute_intraday_features,
    compute_opening_range_features,
    compute_premarket_features,
)

ET = ZoneInfo("America/New_York")


def _bars(start_hour: int, n: int, price: float = 100.0) -> pd.DataFrame:
    base = datetime(2025, 6, 2, start_hour, 0, tzinfo=ET)
    idx = pd.date_range(base, periods=n, freq="1min", tz=ET)
    return pd.DataFrame(
        {
            "Open": price,
            "High": price * 1.01,
            "Low": price * 0.99,
            "Close": price,
            "Volume": 1000,
        },
        index=idx,
    )


class TestIntradayFeatures:
    def test_gap_pct(self):
        assert compute_gap_pct(100, 103) == pytest.approx(3.0)

    def test_premarket_features_empty(self):
        features = compute_premarket_features(pd.DataFrame(), 1_000_000)
        assert features["premarket_volume"] == 0.0

    def test_premarket_features(self):
        pm = _bars(4, 60, price=50)
        features = compute_premarket_features(pm, avg_daily_volume=600_000)
        assert features["premarket_volume"] > 0
        assert features["premarket_volume_ratio"] > 0

    def test_opening_range_features(self):
        # premarket + first hour RTH
        pm = _bars(4, 330, price=100)
        rth = _bars(9, 60, price=100)
        rth.index = rth.index + pd.Timedelta(minutes=30)
        combined = pd.concat([pm, rth])
        features = compute_opening_range_features(combined, trading_date=datetime(2025, 6, 2).date())
        assert "or_5m_range_pct" in features
        assert features["or_5m_range_pct"] >= 0

    def test_compute_intraday_features(self):
        pm = _bars(4, 330)
        rth = _bars(9, 60)
        rth.index = rth.index + pd.Timedelta(minutes=30)
        combined = pd.concat([pm, rth])
        features = compute_intraday_features(combined, prior_close=98.0, avg_daily_volume=1_000_000)
        assert "gap_pct" in features
        assert "premarket_volume_ratio" in features
