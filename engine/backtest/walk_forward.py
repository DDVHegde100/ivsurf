"""Walk-forward validation for time-series ML models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd


@dataclass
class WalkForwardFold:
    train_idx: np.ndarray
    test_idx: np.ndarray
    train_start: Any
    train_end: Any
    test_start: Any
    test_end: Any


def walk_forward_splits(
    n_samples: int,
    train_window: int = 252,
    test_window: int = 21,
    purge_gap: int = 5,
    step: int | None = None,
) -> Iterator[WalkForwardFold]:
    """
    Generate walk-forward train/test index splits.

    Args:
        n_samples: Total number of observations
        train_window: Training window size (days)
        test_window: Test window size (days)
        purge_gap: Gap between train and test to reduce leakage
        step: Step size between folds (defaults to test_window)
    """
    step = step or test_window
    start = train_window + purge_gap

    while start + test_window <= n_samples:
        train_idx = np.arange(start - train_window - purge_gap, start - purge_gap)
        test_idx = np.arange(start, start + test_window)
        yield WalkForwardFold(
            train_idx=train_idx,
            test_idx=test_idx,
            train_start=int(train_idx[0]),
            train_end=int(train_idx[-1]),
            test_start=int(test_idx[0]),
            test_end=int(test_idx[-1]),
        )
        start += step


def precision_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int = 10) -> float:
    """Precision@K for binary labels."""
    if len(y_true) == 0:
        return 0.0
    k = min(k, len(y_true))
    top = np.argsort(y_score)[-k:]
    return float(np.mean(y_true[top]))


def walk_forward_evaluate(
    X: pd.DataFrame,
    y: pd.Series,
    fit_predict_fn: Callable[[pd.DataFrame, pd.Series, pd.DataFrame], np.ndarray],
    train_window: int = 252,
    test_window: int = 21,
    purge_gap: int = 5,
) -> dict[str, Any]:
    """
    Run walk-forward evaluation and aggregate metrics.

    fit_predict_fn(train_X, train_y, test_X) -> predicted probabilities
    """
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    n = len(X)

    precisions: list[float] = []
    hit_rates: list[float] = []

    for fold in walk_forward_splits(n, train_window, test_window, purge_gap):
        train_X = X.iloc[fold.train_idx]
        train_y = y.iloc[fold.train_idx]
        test_X = X.iloc[fold.test_idx]
        test_y = y.iloc[fold.test_idx]

        if train_y.nunique() < 2 or test_y.empty:
            continue

        try:
            probs = fit_predict_fn(train_X, train_y, test_X)
            preds = (probs >= 0.5).astype(int)
            hit_rates.append(float((preds == test_y.values).mean()))
            precisions.append(precision_at_k(test_y.values, probs, k=min(10, len(test_y))))
        except Exception:
            continue

    return {
        "folds_evaluated": len(precisions),
        "mean_hit_rate": float(np.mean(hit_rates)) if hit_rates else 0.0,
        "mean_precision_at_10": float(np.mean(precisions)) if precisions else 0.0,
    }
