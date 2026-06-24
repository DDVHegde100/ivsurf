"""Tests for options-aware opening plays."""

import pandas as pd
import pytest

from engine.signals.opening_options import (
    breakeven_moves,
    enrich_scan_with_options,
    price_straddle,
    price_strangle,
    recommend_from_scan_row,
    recommend_options_play,
)


class TestOpeningOptions:
    def test_no_play_when_or_low(self):
        play = recommend_options_play(spot=100, volatility=0.25, or_15m_range_pct=0.5)
        assert play["play_type"] == "none"

    def test_straddle_on_high_or_small_gap(self):
        play = recommend_options_play(
            spot=100,
            volatility=0.3,
            or_15m_range_pct=2.0,
            gap_pct=0.3,
        )
        assert play["play_type"] == "straddle"
        assert play["call_strike"] == play["put_strike"]
        assert play["estimated_debit"] > 0
        assert play["breakeven_up_pct"] > 0

    def test_strangle_on_moderate_or(self):
        play = recommend_options_play(
            spot=100,
            volatility=0.25,
            or_15m_range_pct=1.2,
            gap_pct=2.0,
        )
        assert play["play_type"] == "strangle"
        assert play["call_strike"] > play["put_strike"]

    def test_price_straddle_positive(self):
        debit = price_straddle(100, 100, 0.25, expiry_days=7)
        assert debit > 0

    def test_price_strangle_cheaper_than_straddle(self):
        straddle = price_straddle(100, 100, 0.25, expiry_days=7)
        strangle = price_strangle(100, 102, 98, 0.25, expiry_days=7)
        assert strangle < straddle

    def test_breakeven_moves_straddle(self):
        up, down = breakeven_moves(100, 5.0, 100, 100, "straddle")
        assert up == pytest.approx(5.0, abs=0.01)
        assert down == pytest.approx(5.0, abs=0.01)

    def test_recommend_from_scan_row(self):
        row = {
            "ticker": "AAPL",
            "price": 150,
            "volatility": 0.28,
            "or_15m_range_pct": 2.5,
            "gap_pct": 0.2,
        }
        play = recommend_from_scan_row(row)
        assert play["play_type"] == "straddle"

    def test_enrich_scan_with_options(self):
        df = pd.DataFrame(
            [
                {"ticker": "AAPL", "price": 100, "volatility": 0.3, "or_15m_range_pct": 2.0, "gap_pct": 0.1},
                {"ticker": "MSFT", "price": 200, "volatility": 0.2, "or_15m_range_pct": 0.3, "gap_pct": 0.5},
            ]
        )
        enriched = enrich_scan_with_options(df)
        assert enriched.iloc[0]["options_play_type"] == "straddle"
        assert enriched.iloc[1]["options_play_type"] == "none"
