"""Walk-forward ML ranker for opening volatility signals."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

from engine.backtest.walk_forward import walk_forward_evaluate

try:
    from xgboost import XGBClassifier

    _HAS_XGB = True
except ImportError:
    _HAS_XGB = False


DEFAULT_FEATURES = [
    "gap_pct",
    "premarket_volume_ratio",
    "premarket_range_pct",
    "or_5m_range_pct",
    "or_15m_range_pct",
    "or_30m_range_pct",
    "relative_volume_open",
    "vwap_deviation_pct",
    "volatility",
    "regime_multiplier",
]


class OpeningMLRanker:
    """Binary classifier ranking opening-hour big movers."""

    def __init__(self, feature_cols: list[str] | None = None, use_xgboost: bool = True):
        self.feature_cols = feature_cols or DEFAULT_FEATURES
        self.use_xgboost = use_xgboost and _HAS_XGB
        self.model = None
        self.scaler = StandardScaler()
        self._fitted = False

    def _build_model(self):
        if self.use_xgboost:
            return XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=42,
            )
        return GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [c for c in self.feature_cols if c in df.columns]
        return df[cols].fillna(0.0)

    def fit(self, df: pd.DataFrame, label_col: str = "label_big_mover_up") -> dict[str, Any]:
        """Train ranker on labeled feature DataFrame."""
        X = self._prepare(df)
        y = df[label_col].astype(int)
        X_scaled = self.scaler.fit_transform(X)

        self.model = self._build_model()
        self.model.fit(X_scaled, y)
        self._fitted = True

        train_probs = self.model.predict_proba(X_scaled)[:, 1]
        return {
            "backend": "xgboost" if self.use_xgboost else "sklearn_gbm",
            "n_samples": len(df),
            "positive_rate": float(y.mean()),
            "train_hit_rate": float(((train_probs >= 0.5).astype(int) == y).mean()),
        }

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self._fitted or self.model is None:
            raise ValueError("Model must be fitted before prediction")
        X = self._prepare(df)
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]

    def rank(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ml_score column and sort descending."""
        out = df.copy()
        out["ml_score"] = self.predict_proba(out) * 100
        return out.sort_values("ml_score", ascending=False).reset_index(drop=True)

    def walk_forward_validate(
        self,
        df: pd.DataFrame,
        label_col: str = "label_big_mover_up",
        train_window: int = 252,
        test_window: int = 21,
    ) -> dict[str, Any]:
        """Walk-forward validation with temporal splits."""

        def fit_predict(train_X, train_y, test_X):
            scaler = StandardScaler()
            X_tr = scaler.fit_transform(self._prepare(train_X))
            X_te = scaler.transform(self._prepare(test_X))
            model = self._build_model()
            model.fit(X_tr, train_y)
            return model.predict_proba(X_te)[:, 1]

        X = self._prepare(df)
        y = df[label_col].astype(int)
        return walk_forward_evaluate(
            X,
            y,
            fit_predict,
            train_window=train_window,
            test_window=test_window,
        )
