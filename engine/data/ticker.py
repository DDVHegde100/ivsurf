"""Ticker-level data assembly for the market scanner."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yfinance as yf

from engine.features.daily import compute_daily_features

if TYPE_CHECKING:
    from engine.signals.swing import SwingSignalEngine


def fetch_ticker_data(ticker: str, signal_engine: SwingSignalEngine) -> dict[str, Any] | None:
    """Fetch comprehensive data for a single ticker with predictive analysis."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="30d", interval="1d")
        if hist.empty or len(hist) < 10:
            return None

        current_price = hist["Close"].iloc[-1]
        if current_price < 1.0 or current_price > 5000:
            return None

        info = stock.info
        if not info or info.get("regularMarketPrice") is None:
            return None

        hist_long = stock.history(period="1y", interval="1d")
        features = compute_daily_features(hist, hist_long)

        gain_prediction_score = signal_engine.calculate_tomorrow_gain_prediction(
            hist,
            features["current_price"],
            features["volatility"],
            features["rsi"],
            features["macd_histogram"],
            features["bb_position"],
            features["volume_trend"],
            features["momentum_1d"],
            features["momentum_3d"],
            features["momentum_5d"],
        )

        gain_potential = signal_engine.calculate_tomorrow_gain_potential(
            hist,
            features["current_price"],
            features["volatility"],
            gain_prediction_score,
        )

        yesterday_volatility_score = min(features["volatility"] * 100, 100)
        yesterday_volume_score = min(features["volume_ratio"] * 50, 100)
        yesterday_momentum_score = min(abs(features["price_change_pct"]) * 10, 100)
        yesterday_profit_score = (
            yesterday_volatility_score + yesterday_volume_score + yesterday_momentum_score
        ) / 3

        options_score = yesterday_volatility_score * 1.5 + yesterday_momentum_score * 0.5
        options_prediction = gain_prediction_score * 1.2 + features["volatility"] * 50

        return {
            "ticker": ticker,
            "price": features["current_price"],
            "change": features["price_change"],
            "change_pct": features["price_change_pct"],
            "volume": features["current_volume"],
            "volume_ratio": features["volume_ratio"],
            "volume_trend": features["volume_trend"],
            "volatility": features["volatility"],
            "rsi": features["rsi"],
            "macd": features["macd_histogram"],
            "bb_position": features["bb_position"],
            "momentum_1d": features["momentum_1d"],
            "momentum_3d": features["momentum_3d"],
            "momentum_5d": features["momentum_5d"],
            "sma_5": features["sma_5"],
            "sma_20": features["sma_20"],
            "yesterday_profit_score": yesterday_profit_score,
            "tomorrow_gain_score": gain_prediction_score,
            "options_score": options_score,
            "options_prediction": options_prediction,
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "expected_gain_pct": gain_potential["expected_gain_pct"],
            "median_gain_pct": gain_potential["median_gain_pct"],
            "conservative_target": gain_potential["conservative_target"],
            "moderate_target": gain_potential["moderate_target"],
            "aggressive_target": gain_potential["aggressive_target"],
            "probability_positive": gain_potential["probability_positive"],
            "confidence_level": gain_potential["confidence_level"],
            "risk_reward_ratio": gain_potential["risk_reward_ratio"],
            "expected_category": gain_potential["expected_category"],
            "expected_low": gain_potential["expected_low"],
            "expected_medium": gain_potential["expected_medium"],
            "expected_high": gain_potential["expected_high"],
            "average_gain_pct": gain_potential["average_gain_pct"],
            "sharpe_estimate": gain_potential["sharpe_estimate"],
            "max_drawdown_risk": gain_potential["max_drawdown_risk"],
            "value_at_risk_5pct": gain_potential["value_at_risk_5pct"],
        }

    except Exception:
        return None
