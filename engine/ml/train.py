"""Train and persist the opening ML ranker from stored signal outcomes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.data.storage import DataStore
from engine.ml.dataset import build_training_dataset
from engine.signals.ml_ranker import OpeningMLRanker, default_model_path


def train_ranker_from_store(
    store: DataStore | None = None,
    *,
    horizon: str = "1h",
    min_samples: int = 30,
    model_path: str | Path | None = None,
    use_xgboost: bool = True,
    walk_forward: bool = True,
) -> dict[str, Any]:
    """
    Train OpeningMLRanker on labeled signals in SQLite/Postgres.

    Returns training metrics and walk-forward validation when enough data exists.
    """
    store = store or DataStore()
    rows = store.fetch_labeled_signals(horizon=horizon)
    df = build_training_dataset(rows)

    if len(df) < min_samples:
        return {
            "trained": False,
            "reason": "insufficient_samples",
            "n_samples": len(df),
            "min_samples": min_samples,
        }

    if df["label_big_mover_up"].nunique() < 2:
        return {
            "trained": False,
            "reason": "single_class_labels",
            "n_samples": len(df),
            "positive_rate": float(df["label_big_mover_up"].mean()),
        }

    ranker = OpeningMLRanker(use_xgboost=use_xgboost)
    fit_metrics = ranker.fit(df)

    out_path = ranker.save(model_path or default_model_path())

    result: dict[str, Any] = {
        "trained": True,
        "model_path": str(out_path),
        "horizon": horizon,
        **fit_metrics,
    }

    if walk_forward and len(df) >= 80:
        train_window = min(252, max(40, len(df) // 2))
        result["walk_forward"] = ranker.walk_forward_validate(
            df,
            train_window=train_window,
            test_window=min(21, max(5, len(df) // 10)),
        )

    return result
