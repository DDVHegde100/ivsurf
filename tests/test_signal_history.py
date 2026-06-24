"""Tests for signal history analytics."""

import pandas as pd

from engine.analytics.signal_history import (
    build_equity_curve,
    compute_hit_rates,
    directional_return,
    parse_signal_history,
)


class TestSignalHistory:
    def test_directional_return(self):
        assert directional_return(0.05, "up") == 0.05
        assert directional_return(0.05, "down") == -0.05

    def test_parse_signal_history(self):
        rows = [
            {
                "id": 1,
                "ticker": "AAPL",
                "signal_type": "opening_scan",
                "score": 70.0,
                "payload": '{"gap_pct": 2.0, "direction": "up"}',
                "created_at": "2025-06-01 09:35:00",
                "horizon": "1d",
                "realized_return": 0.04,
                "outcome_label": "big_mover_up",
            },
            {
                "id": 1,
                "ticker": "AAPL",
                "signal_type": "opening_scan",
                "score": 70.0,
                "payload": '{"gap_pct": 2.0, "direction": "up"}',
                "created_at": "2025-06-01 09:35:00",
                "horizon": None,
                "realized_return": None,
                "outcome_label": None,
            },
        ]
        signals, outcomes = parse_signal_history(rows)
        assert len(signals) == 1
        assert signals.iloc[0]["direction"] == "up"
        assert len(outcomes) == 1

    def test_build_equity_curve(self):
        signals = pd.DataFrame(
            [
                {"id": 1, "ticker": "AAPL", "created_at": "2025-06-01", "direction": "up"},
                {"id": 2, "ticker": "MSFT", "created_at": "2025-06-02", "direction": "down"},
            ]
        )
        outcomes = pd.DataFrame(
            [
                {"signal_id": 1, "horizon": "1d", "realized_return": 0.10, "outcome_label": "big_mover_up"},
                {"signal_id": 2, "horizon": "1d", "realized_return": 0.04, "outcome_label": "big_mover_up"},
            ]
        )
        curve = build_equity_curve(
            outcomes,
            signals,
            horizon="1d",
            initial_equity=10_000,
            notional_per_trade=1_000,
        )
        assert len(curve) == 2
        assert curve.iloc[0]["equity"] == 10_100
        assert curve.iloc[1]["equity"] == 10_060  # short loses when underlying up 4%

    def test_compute_hit_rates(self):
        signals = pd.DataFrame(
            [
                {"id": 1, "direction": "up"},
                {"id": 2, "direction": "up"},
            ]
        )
        outcomes = pd.DataFrame(
            [
                {"signal_id": 1, "horizon": "1d", "realized_return": 0.05, "outcome_label": "big_mover_up"},
                {"signal_id": 2, "horizon": "1d", "realized_return": -0.02, "outcome_label": "flat"},
            ]
        )
        stats = compute_hit_rates(outcomes, signals, horizon="1d")
        assert stats["trades"] == 2
        assert stats["win_rate"] == 0.5
