"""Tests for opening range feed and websocket."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from engine.feed.opening_range import OpeningRangeFeed, build_opening_range_snapshot

ET = ZoneInfo("America/New_York")


def _bars(start_hour: int, n: int, price: float = 100.0) -> pd.DataFrame:
    base = datetime(2025, 6, 2, start_hour, 0, tzinfo=ET)
    idx = pd.date_range(base, periods=n, freq="1min", tz=ET)
    return pd.DataFrame(
        {
            "Open": price,
            "High": price * 1.02,
            "Low": price * 0.98,
            "Close": price * 1.01,
            "Volume": 1000,
        },
        index=idx,
    )


class TestOpeningRangeSnapshot:
    def test_build_snapshot_includes_windows(self):
        pm = _bars(4, 330, price=100)
        rth = _bars(9, 45, price=100)
        rth.index = rth.index + pd.Timedelta(minutes=30)
        combined = pd.concat([pm, rth])

        snapshot = build_opening_range_snapshot(
            "TEST",
            combined,
            prior_close=98.0,
            avg_daily_volume=1_000_000,
            trading_date=datetime(2025, 6, 2).date(),
        )

        assert snapshot is not None
        assert snapshot["ticker"] == "TEST"
        assert snapshot["gap_pct"] > 0
        assert "5m" in snapshot["windows"]
        assert "15m" in snapshot["windows"]
        assert snapshot["breakout"] in {"above", "below", "inside"}

    def test_empty_bars_returns_none(self):
        assert build_opening_range_snapshot("X", pd.DataFrame(), prior_close=1, avg_daily_volume=1) is None


class TestOpeningRangeFeed:
    def test_snapshots_use_fetcher(self):
        pm = _bars(4, 330)
        rth = _bars(9, 45)
        rth.index = rth.index + pd.Timedelta(minutes=30)
        bars = pd.concat([pm, rth])

        class FakeFetcher:
            def get_bars(self, ticker, **kwargs):
                return bars

        feed = OpeningRangeFeed(fetcher=FakeFetcher())
        with patch.object(feed, "_daily_stats", return_value=(98.0, 1_000_000)):
            rows = feed.snapshots(["AAA", "AAA"])

        assert len(rows) == 1
        assert rows[0]["ticker"] == "AAA"


class TestOpeningRangeWebSocket:
    @pytest.fixture
    def ws_client(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    def test_ws_subscribe_and_update(self, ws_client):
        fake_snapshot = [
            {
                "ticker": "TEST",
                "day_open": 100.0,
                "last_price": 101.0,
                "windows": {"15m": {"high": 102, "low": 98, "range_pct": 4.0}},
            }
        ]

        with patch("api.routes.opening_range_ws.OpeningRangeFeed") as mock_cls:
            mock_cls.return_value.snapshots.return_value = fake_snapshot
            with ws_client.websocket_connect("/ws/opening-range") as ws:
                ws.send_json({"action": "subscribe", "tickers": ["TEST"], "interval_sec": 5})
                subscribed = ws.receive_json()
                assert subscribed["type"] == "subscribed"
                assert subscribed["tickers"] == ["TEST"]

                update = ws.receive_json()
                assert update["type"] == "update"
                assert update["count"] == 1
                assert update["snapshots"][0]["ticker"] == "TEST"

    def test_ws_rejects_missing_key_when_auth_enabled(self, ws_client, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        with ws_client.websocket_connect("/ws/opening-range") as ws:
            with pytest.raises(Exception):
                ws.receive_json()

    def test_ws_accepts_valid_key(self, ws_client, monkeypatch):
        monkeypatch.setenv("IVSURF_API_KEY", "secret")
        with patch("api.routes.opening_range_ws.OpeningRangeFeed") as mock_cls:
            mock_cls.return_value.snapshots.return_value = []
            with ws_client.websocket_connect("/ws/opening-range?api_key=secret") as ws:
                ws.send_json({"action": "subscribe", "tickers": ["TEST"], "interval_sec": 5})
                assert ws.receive_json()["type"] == "subscribed"
