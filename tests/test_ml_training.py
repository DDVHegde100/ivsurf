"""Tests for ML training from stored signals."""

import json

import numpy as np
import pandas as pd
import pytest

from engine.ml.dataset import build_training_dataset
from engine.ml.train import train_ranker_from_store
from engine.signals.ml_ranker import OpeningMLRanker, load_ranker_if_available


def _feature_payload(**overrides) -> dict:
    base = {
        "gap_pct": 2.0,
        "premarket_volume_ratio": 0.5,
        "premarket_range_pct": 1.0,
        "or_5m_range_pct": 0.8,
        "or_15m_range_pct": 1.2,
        "or_30m_range_pct": 1.5,
        "relative_volume_open": 1.8,
        "vwap_deviation_pct": 0.3,
        "volatility": 0.25,
        "regime_multiplier": 1.0,
    }
    base.update(overrides)
    return base


class TestMLDataset:
    def test_build_training_dataset_from_labels(self):
        rows = [
            {
                "id": 1,
                "ticker": "AAPL",
                "payload": json.dumps(_feature_payload()),
                "created_at": "2025-06-01",
                "outcome_label": "big_mover_up",
                "realized_return": 0.04,
            },
            {
                "id": 2,
                "ticker": "MSFT",
                "payload": json.dumps(_feature_payload(gap_pct=0.2)),
                "created_at": "2025-06-02",
                "outcome_label": "flat",
                "realized_return": 0.005,
            },
        ]
        df = build_training_dataset(rows)
        assert len(df) == 2
        assert df.iloc[0]["label_big_mover_up"] == 1
        assert df.iloc[1]["label_big_mover_up"] == 0

    def test_build_training_dataset_from_return_fallback(self):
        rows = [
            {
                "id": 1,
                "ticker": "AAPL",
                "payload": json.dumps(_feature_payload()),
                "created_at": "2025-06-01",
                "outcome_label": None,
                "realized_return": 0.05,
            }
        ]
        df = build_training_dataset(rows)
        assert df.iloc[0]["label_big_mover_up"] == 1


class TestMLTraining:
    def _seed_labeled_store(self, store, n: int = 40):
        rng = np.random.default_rng(7)
        for i in range(n):
            payload = _feature_payload(
                gap_pct=float(rng.normal(0, 2)),
                relative_volume_open=float(rng.uniform(0.8, 2.5)),
            )
            signal_id = store.log_signal(f"T{i % 5}", "opening_scan", 60.0, payload)
            label = "big_mover_up" if payload["gap_pct"] > 1.0 else "flat"
            ret = 0.04 if label == "big_mover_up" else 0.005
            store.log_outcome(signal_id, "1h", ret, label)

    def test_train_ranker_from_store(self, tmp_path):
        db = tmp_path / "train.db"
        from engine.data.storage import DataStore

        store = DataStore(db_path=db)
        self._seed_labeled_store(store, n=50)

        model_path = tmp_path / "model.joblib"
        summary = train_ranker_from_store(
            store,
            min_samples=30,
            model_path=model_path,
            use_xgboost=False,
            walk_forward=False,
        )
        assert summary["trained"] is True
        assert model_path.exists()

        ranker = OpeningMLRanker.load(model_path)
        sample = pd.DataFrame([_feature_payload()])
        scores = ranker.predict_proba(sample)
        assert len(scores) == 1

    def test_train_insufficient_samples(self, tmp_path):
        from engine.data.storage import DataStore

        store = DataStore(db_path=tmp_path / "small.db")
        self._seed_labeled_store(store, n=5)

        summary = train_ranker_from_store(store, min_samples=30, use_xgboost=False, walk_forward=False)
        assert summary["trained"] is False
        assert summary["reason"] == "insufficient_samples"

    def test_save_load_roundtrip(self, tmp_path):
        df = pd.DataFrame(
            {
                "gap_pct": [1.0, -0.5, 2.0, 0.1],
                "premarket_volume_ratio": [0.5, 0.4, 0.8, 0.3],
                "premarket_range_pct": [1.0, 0.8, 1.5, 0.6],
                "or_5m_range_pct": [0.5, 0.4, 1.0, 0.3],
                "or_15m_range_pct": [1.0, 0.7, 1.2, 0.4],
                "or_30m_range_pct": [1.2, 0.9, 1.4, 0.5],
                "relative_volume_open": [1.5, 1.0, 2.0, 0.9],
                "vwap_deviation_pct": [0.2, -0.1, 0.4, 0.0],
                "volatility": [0.2, 0.25, 0.3, 0.22],
                "regime_multiplier": [1.0, 1.0, 0.9, 1.0],
                "label_big_mover_up": [1, 0, 1, 0],
            }
        )
        ranker = OpeningMLRanker(use_xgboost=False)
        ranker.fit(df)
        path = tmp_path / "ranker.joblib"
        ranker.save(path)

        loaded = OpeningMLRanker.load(path)
        np.testing.assert_allclose(
            ranker.predict_proba(df),
            loaded.predict_proba(df),
        )

    def test_load_ranker_if_available_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("IVSURF_MODEL_PATH", str(tmp_path / "missing.joblib"))
        assert load_ranker_if_available() is None
