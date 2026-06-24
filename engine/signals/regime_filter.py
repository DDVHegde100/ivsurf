"""Regime-aware gating and score scaling for signal pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from models.garch import GARCHModel
from models.regime_switching import MarkovRegimeSwitching


class RegimeFilter:
    """
    Filter and scale signals based on market regime and GARCH vol forecast.

    High-volatility regimes receive full weight; low-vol regimes are dampened.
    """

    def __init__(self, n_regimes: int = 2, min_returns: int = 60):
        self.n_regimes = n_regimes
        self.min_returns = min_returns
        self._regime_model: MarkovRegimeSwitching | None = None
        self._garch_model: GARCHModel | None = None
        self._high_vol_regime_id: int | None = None

    def fit(self, returns: pd.Series | np.ndarray) -> dict:
        """Fit regime switching and GARCH on historical returns."""
        ret = np.asarray(returns)[-252:]
        ret = ret[~np.isnan(ret)]
        if len(ret) < self.min_returns:
            return {"fitted": False}

        self._regime_model = MarkovRegimeSwitching(n_regimes=self.n_regimes)
        self._regime_model.fit(ret)

        # Identify high-volatility regime by variance
        stats = self._regime_model.regime_statistics()
        vols = {v["regime_id"]: v["volatility"] for v in stats.values()}
        self._high_vol_regime_id = max(vols, key=vols.get)

        self._garch_model = GARCHModel()
        try:
            self._garch_model.fit(ret)
        except Exception:
            self._garch_model = None

        return {"fitted": True, "high_vol_regime": self._high_vol_regime_id}

    def evaluate(self, returns: pd.Series | np.ndarray) -> dict:
        """
        Return regime label, GARCH forecast, and score multiplier for latest window.
        """
        ret = np.asarray(returns)[-252:]
        ret = ret[~np.isnan(ret)]

        if self._regime_model is None or not self._regime_model.fitted:
            try:
                self.fit(ret)
            except Exception:
                return {
                    "regime_label": "unknown",
                    "high_vol_probability": 0.5,
                    "score_multiplier": 1.0,
                    "garch_forecast": None,
                    "allow_signal": True,
                }

        probs = self._regime_model.get_regime_probabilities(ret)
        current = probs[-1]
        high_vol_prob = float(current[self._high_vol_regime_id]) if self._high_vol_regime_id is not None else 0.5

        if high_vol_prob >= 0.6:
            label = "high_vol"
            multiplier = 1.0 + (high_vol_prob - 0.6) * 0.5
        elif high_vol_prob <= 0.35:
            label = "low_vol"
            multiplier = 0.5 + high_vol_prob
        else:
            label = "neutral"
            multiplier = 0.85

        garch_forecast = None
        if self._garch_model and self._garch_model.fitted:
            try:
                garch_forecast = float(self._garch_model.forecast_volatility(steps=1)[0])
            except Exception:
                garch_forecast = None

        return {
            "regime_label": label,
            "high_vol_probability": high_vol_prob,
            "score_multiplier": float(min(1.3, max(0.4, multiplier))),
            "garch_forecast": garch_forecast,
            "allow_signal": high_vol_prob >= 0.35 or label != "low_vol",
        }
