"""Tests for SQLite data store."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from engine.data.storage import DataStore


@pytest.fixture
def store(tmp_path):
    return DataStore(db_path=tmp_path / "test.db")


class TestDataStore:
    def test_save_and_load_bars(self, store):
        idx = pd.date_range("2025-06-02 09:30", periods=5, freq="1min", tz="America/New_York")
        df = pd.DataFrame(
            {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 1000},
            index=idx,
        )
        n = store.save_bars("AAPL", df)
        assert n == 5

        loaded = store.load_bars("AAPL")
        assert len(loaded) == 5
        assert loaded["Close"].iloc[-1] == 1.5

    def test_log_signal_and_outcome(self, store):
        signal_id = store.log_signal("TSLA", "opening_scan", 85.5, {"gap_pct": 2.1})
        assert signal_id > 0
        store.log_outcome(signal_id, "1h", 0.015, label="big_mover_up")

    def test_save_bars_parquet(self, store):
        pytest.importorskip("pyarrow")
        idx = pd.date_range("2025-06-02 09:30", periods=3, freq="1min", tz="America/New_York")
        df = pd.DataFrame(
            {"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 100},
            index=idx,
        )
        path = store.save_bars_parquet("NVDA", df)
        assert Path(path).exists()
