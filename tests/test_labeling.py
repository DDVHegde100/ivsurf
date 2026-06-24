"""Tests for signal outcome labeling."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from engine.backtest.labeling import compute_horizon_return, label_return, label_signal_outcomes

ET = ZoneInfo("America/New_York")


class TestLabeling:
    def test_label_return(self):
        assert label_return(0.04) == "big_mover_up"
        assert label_return(-0.05) == "big_mover_down"
        assert label_return(0.01) == "flat"

    def test_compute_horizon_return_1h(self):
        open_dt = datetime(2025, 6, 2, 9, 30, tzinfo=ET)
        idx = pd.date_range(open_dt, periods=60, freq="1min", tz=ET)
        intraday = pd.DataFrame(
            {
                "Open": 100.0,
                "High": 104.0,
                "Low": 99.0,
                "Close": 103.0,
                "Volume": 1000,
            },
            index=idx,
        )
        ret = compute_horizon_return(
            intraday,
            pd.DataFrame(),
            entry_price=100.0,
            horizon="1h",
            signal_date=pd.Timestamp(open_dt),
        )
        assert ret == pytest.approx(0.03)

    def test_label_signal_outcomes(self):
        open_dt = datetime(2025, 6, 2, 9, 30, tzinfo=ET)
        idx = pd.date_range(open_dt, periods=60, freq="1min", tz=ET)
        intraday = pd.DataFrame(
            {"Open": 100, "High": 104, "Low": 99, "Close": 104, "Volume": 1000},
            index=idx,
        )
        daily_idx = pd.date_range("2025-06-02", periods=5, freq="D", tz=ET)
        daily = pd.DataFrame({"Close": [100, 104, 108, 106, 110]}, index=daily_idx)

        result = label_signal_outcomes(intraday, daily, 100.0, pd.Timestamp(open_dt))
        assert result["big_mover_up"] is True
        assert result["outcomes"]["1h"]["label"] == "big_mover_up"
