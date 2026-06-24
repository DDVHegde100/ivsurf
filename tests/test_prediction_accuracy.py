#!/usr/bin/env python3
"""
Tests for swing trading prediction heuristics in RetroTerminal.

Unit tests use synthetic data (no network). Integration tests marked separately.
"""

import os
import sys
import unittest

import numpy as np
import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ivsurf_retro_terminal import RetroTerminal


def _make_synthetic_hist(n_days: int = 100, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    prices = [100.0]
    for _ in range(n_days - 1):
        prices.append(prices[-1] * (1 + rng.normal(0.001, 0.02)))

    return pd.DataFrame(
        {
            "Close": prices,
            "High": [p * 1.01 for p in prices],
            "Low": [p * 0.99 for p in prices],
            "Volume": [1_000_000 + rng.integers(-200_000, 200_000) for _ in range(n_days)],
        }
    )


def _gain_keys(predictions: dict) -> dict:
    """Map gain-potential output to legacy key names used in assertions."""
    return {
        "predicted_low": predictions["conservative_target"],
        "predicted_high": predictions["aggressive_target"],
        "predicted_median": predictions["moderate_target"],
        "confidence_level": predictions["confidence_level"],
        "expected_return": predictions["expected_gain_pct"],
    }


class TestSwingPredictionUnit(unittest.TestCase):
    """Fast unit tests using synthetic data."""

    def setUp(self):
        self.terminal = RetroTerminal()
        self.hist = _make_synthetic_hist()
        self.current_price = self.hist["Close"].iloc[-1]
        self.volatility = self.hist["Close"].pct_change().std() * np.sqrt(252)

    def test_prediction_score_bounds(self):
        score = self.terminal.calculate_tomorrow_gain_prediction(
            self.hist,
            self.current_price,
            self.volatility,
            rsi=35,
            macd=0.01,
            bb_position=0.2,
            volume_trend=1.8,
            momentum_1d=1.5,
            momentum_3d=2.0,
            momentum_5d=3.0,
        )
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)

    def test_gain_potential_structure(self):
        score = 75
        predictions = self.terminal.calculate_tomorrow_gain_potential(
            self.hist, self.current_price, self.volatility, score
        )
        mapped = _gain_keys(predictions)

        self.assertIn("conservative_target", predictions)
        self.assertIn("aggressive_target", predictions)
        self.assertIn("confidence_level", predictions)
        self.assertGreater(mapped["predicted_high"], mapped["predicted_low"])
        self.assertGreaterEqual(mapped["confidence_level"], 60)
        self.assertLessEqual(mapped["confidence_level"], 95)

    def test_market_condition_variants(self):
        conditions = [
            {"rsi": 25, "macd": 0.01, "bb_position": 0.1, "volume_trend": 2.0},
            {"rsi": 72, "macd": -0.01, "bb_position": 0.9, "volume_trend": 1.2},
            {"rsi": 50, "macd": 0.005, "bb_position": 0.5, "volume_trend": 1.0},
        ]
        for condition in conditions:
            score = self.terminal.calculate_tomorrow_gain_prediction(
                self.hist,
                self.current_price,
                self.volatility,
                condition["rsi"],
                condition["macd"],
                condition["bb_position"],
                condition["volume_trend"],
                1.0,
                2.0,
                3.0,
            )
            self.assertGreaterEqual(score, 0)

    def test_edge_cases(self):
        minimal_hist = pd.DataFrame(
            {
                "Close": [100, 101, 102],
                "High": [101, 102, 103],
                "Low": [99, 100, 101],
                "Volume": [1000, 1100, 1200],
            }
        )
        score = self.terminal.calculate_tomorrow_gain_prediction(
            minimal_hist, 102, 0.2, 50, 0, 0.5, 1.0, 1.0, 1.0, 2.0
        )
        self.assertIsInstance(score, (int, float))

        extreme_score = self.terminal.calculate_tomorrow_gain_prediction(
            minimal_hist, 102, 2.0, 50, 0, 0.5, 1.0, 1.0, 1.0, 2.0
        )
        self.assertIsInstance(extreme_score, (int, float))

    def test_confidence_scales_with_score(self):
        low = self.terminal.calculate_tomorrow_gain_potential(
            self.hist, self.current_price, self.volatility, 30
        )
        high = self.terminal.calculate_tomorrow_gain_potential(
            self.hist, self.current_price, self.volatility, 90
        )
        self.assertGreaterEqual(
            high["confidence_level"],
            low["confidence_level"] - 5,
            "Higher prediction scores should not reduce confidence",
        )


@pytest.mark.integration
class TestSwingPredictionIntegration(unittest.TestCase):
    """Live market data tests — run with: pytest -m integration"""

    def setUp(self):
        yfinance = pytest.importorskip("yfinance")
        self.yf = yfinance
        self.terminal = RetroTerminal()
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]

    def test_live_ticker_pipeline(self):
        ticker = self.test_tickers[0]
        stock = self.yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        if len(hist) <= 30:
            self.skipTest("Insufficient live data")

        current_price = hist["Close"].iloc[-1]
        volatility = hist["Close"].pct_change().std() * np.sqrt(252)

        score = self.terminal.calculate_tomorrow_gain_prediction(
            hist,
            current_price,
            volatility,
            rsi=50,
            macd=0,
            bb_position=0.5,
            volume_trend=1.0,
            momentum_1d=0.5,
            momentum_3d=1.0,
            momentum_5d=1.5,
        )
        predictions = self.terminal.calculate_tomorrow_gain_potential(
            hist, current_price, volatility, score
        )

        self.assertGreaterEqual(score, 0)
        self.assertIn("conservative_target", predictions)


if __name__ == "__main__":
    unittest.main()
