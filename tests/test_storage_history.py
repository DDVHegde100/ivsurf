"""Tests for DataStore signal history queries."""

import json

from engine.data.storage import DataStore


class TestDataStoreSignalHistory:
    def test_fetch_signals_with_outcomes(self, tmp_path):
        db = tmp_path / "test.db"
        store = DataStore(db)

        payload = {"gap_pct": 2.5, "direction": "up"}
        signal_id = store.log_signal("AAPL", "opening_scan", 72.0, payload)
        store.log_outcome(signal_id, "1d", 0.035, "big_mover_up")

        rows = store.fetch_signals_with_outcomes()
        assert len(rows) >= 1
        assert rows[0]["ticker"] == "AAPL"
        assert rows[0]["realized_return"] == 0.035

    def test_fetch_filters_by_signal_type(self, tmp_path):
        db = tmp_path / "test.db"
        store = DataStore(db)
        store.log_signal("AAPL", "opening_scan", 60.0, {})
        store.log_signal("MSFT", "premarket_scan", 55.0, {})

        opening = store.fetch_signals_with_outcomes(signal_type="opening_scan")
        assert all(r["signal_type"] == "opening_scan" for r in opening)
        assert len(opening) == 1
