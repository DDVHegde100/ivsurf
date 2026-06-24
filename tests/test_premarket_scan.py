"""Tests for pre-market scan job."""

from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from engine.data.universe import DEFAULT_UNIVERSE
from engine.jobs.premarket_scan import run_premarket_scan, write_scan_report

ET = ZoneInfo("America/New_York")


class TestPremarketScan:
    def test_skips_weekend(self):
        saturday = datetime(2025, 6, 21, 8, 0, tzinfo=ET)
        summary = run_premarket_scan(as_of=saturday)
        assert summary["skipped"] is True
        assert summary["reason"] == "non_trading_day"

    def test_force_runs_on_weekend(self, monkeypatch):
        saturday = datetime(2025, 6, 21, 8, 0, tzinfo=ET)
        fake_df = pd.DataFrame(
            [{"ticker": "AAPL", "opening_score": 55.0, "gap_pct": 2.0, "direction": "up"}]
        )
        monkeypatch.setattr(
            "engine.jobs.premarket_scan.scan_universe",
            lambda *a, **k: fake_df,
        )
        monkeypatch.setattr(
            "engine.jobs.premarket_scan.DataStore",
            lambda *a, **k: MagicMock(log_signal=lambda *a, **k: 1),
        )

        summary = run_premarket_scan(
            ["AAPL"],
            skip_non_trading_days=False,
            as_of=saturday,
        )
        assert summary["skipped"] is False
        assert summary["count"] == 1

    def test_persists_top_n(self, monkeypatch):
        monday = datetime(2025, 6, 23, 8, 0, tzinfo=ET)
        rows = [
            {"ticker": f"T{i}", "opening_score": 80 - i, "gap_pct": 1.0, "direction": "up"}
            for i in range(5)
        ]
        monkeypatch.setattr(
            "engine.jobs.premarket_scan.scan_universe",
            lambda *a, **k: pd.DataFrame(rows),
        )

        logged: list[str] = []

        class FakeStore:
            def log_signal(self, ticker, signal_type, score, payload):
                logged.append(ticker)
                return len(logged)

        monkeypatch.setattr("engine.jobs.premarket_scan.DataStore", lambda *a, **k: FakeStore())

        summary = run_premarket_scan(["T0", "T1", "T2", "T3", "T4"], top_n=2, as_of=monday)
        assert summary["count"] == 5
        assert len(summary["signal_ids"]) == 2
        assert logged == ["T0", "T1"]

    def test_write_scan_report(self, tmp_path):
        summary = {"count": 1, "results": [{"ticker": "AAPL"}]}
        path = write_scan_report(summary, tmp_path / "scan.json")
        assert path.exists()
        assert "AAPL" in path.read_text()

    def test_default_universe_not_empty(self):
        assert len(DEFAULT_UNIVERSE) >= 10

    def test_cli_main_weekend_skip(self, monkeypatch, capsys, tmp_path):
        from scripts.run_premarket_scan import main

        saturday = datetime(2025, 6, 21, 8, 0, tzinfo=ET)
        monkeypatch.setattr(
            "engine.jobs.premarket_scan.datetime",
            MagicMock(now=lambda tz=None: saturday),
        )
        out = tmp_path / "scan.json"
        code = main(["--output", str(out)])
        assert code == 0
        assert "non_trading_day" in out.read_text()
