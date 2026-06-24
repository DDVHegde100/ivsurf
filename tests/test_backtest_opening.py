"""Tests for walk-forward validation and ML ranker."""

import numpy as np
import pandas as pd
import pytest

from engine.backtest.walk_forward import walk_forward_splits, precision_at_k
from engine.signals.ml_ranker import OpeningMLRanker
from engine.signals.regime_filter import RegimeFilter


class TestWalkForward:
    def test_walk_forward_splits(self):
        folds = list(walk_forward_splits(400, train_window=252, test_window=21, purge_gap=5))
        assert len(folds) > 0
        fold = folds[0]
        assert len(fold.train_idx) == 252
        assert len(fold.test_idx) == 21

    def test_precision_at_k(self):
        y = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        scores = np.array([0.1, 0.9, 0.8, 0.2, 0.7, 0.3, 0.6, 0.4, 0.95, 0.05])
        p = precision_at_k(y, scores, k=3)
        assert 0 <= p <= 1


class TestOpeningMLRanker:
    def _synthetic_labeled_df(self, n: int = 300) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        df = pd.DataFrame(
            {
                "gap_pct": rng.normal(0, 2, n),
                "premarket_volume_ratio": rng.uniform(0, 1, n),
                "premarket_range_pct": rng.uniform(0, 3, n),
                "or_5m_range_pct": rng.uniform(0, 2, n),
                "or_15m_range_pct": rng.uniform(0, 3, n),
                "or_30m_range_pct": rng.uniform(0, 4, n),
                "relative_volume_open": rng.uniform(0.5, 3, n),
                "vwap_deviation_pct": rng.normal(0, 1, n),
                "volatility": rng.uniform(0.15, 0.5, n),
                "regime_multiplier": rng.uniform(0.5, 1.2, n),
            }
        )
        df["label_big_mover_up"] = (
            (df["gap_pct"].abs() > 1.5) & (df["relative_volume_open"] > 1.5)
        ).astype(int)
        return df

    def test_fit_and_rank(self):
        df = self._synthetic_labeled_df(200)
        ranker = OpeningMLRanker(use_xgboost=False)
        metrics = ranker.fit(df)
        assert metrics["n_samples"] == 200
        ranked = ranker.rank(df.head(20))
        assert "ml_score" in ranked.columns
        assert ranked["ml_score"].is_monotonic_decreasing

    def test_walk_forward_validate(self):
        df = self._synthetic_labeled_df(400)
        ranker = OpeningMLRanker(use_xgboost=False)
        result = ranker.walk_forward_validate(df, train_window=200, test_window=21)
        assert "mean_hit_rate" in result


class TestRegimeFilter:
    def test_regime_filter_fit_and_evaluate(self):
        rng = np.random.default_rng(0)
        returns = pd.Series(rng.normal(0, 0.02, 200))
        # inject high-vol cluster
        returns.iloc[100:130] = rng.normal(0, 0.06, 30)

        filt = RegimeFilter()
        fit = filt.fit(returns)
        assert fit["fitted"] is True

        result = filt.evaluate(returns)
        assert "score_multiplier" in result
        assert 0.4 <= result["score_multiplier"] <= 1.3
