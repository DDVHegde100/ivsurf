"""Tests for opening volatility scanner."""

import pytest

from engine.signals.opening_scanner import score_opening_features


class TestOpeningScanner:
    def test_score_high_gap_and_volume(self):
        features = {
            "gap_pct": 4.0,
            "premarket_volume_ratio": 0.8,
            "or_15m_range_pct": 2.5,
            "relative_volume_open": 2.0,
        }
        score = score_opening_features(features, regime_multiplier=1.0)
        assert score > 40

    def test_score_dampened_by_regime(self):
        features = {
            "gap_pct": 3.0,
            "premarket_volume_ratio": 0.5,
            "or_15m_range_pct": 1.5,
            "relative_volume_open": 1.5,
        }
        full = score_opening_features(features, 1.0)
        damped = score_opening_features(features, 0.5)
        assert damped < full

    def test_low_activity_low_score(self):
        features = {
            "gap_pct": 0.2,
            "premarket_volume_ratio": 0.05,
            "or_15m_range_pct": 0.1,
            "relative_volume_open": 0.8,
        }
        assert score_opening_features(features) < 15
