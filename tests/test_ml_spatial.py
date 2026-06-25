"""Tests for ML feature space and terrain modules."""

import pandas as pd
import pytest

from engine.spatial.ml_feature_space import pca_to_3d, scan_results_to_feature_space
from engine.spatial.opening_terrain import build_opening_terrain
from visuals.plot_3d.ml_landscape import synthetic_loss_landscape


def _sample_scan() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "NVDA", "TSLA", "XOM"],
            "gap_pct": [1.2, 3.5, -2.0, 0.5],
            "premarket_volume_ratio": [0.4, 0.9, 0.6, 0.2],
            "or_15m_range_pct": [1.0, 2.5, 1.8, 0.7],
            "relative_volume_open": [1.2, 2.1, 1.5, 0.9],
            "volatility": [0.25, 0.45, 0.55, 0.20],
            "opening_score": [55, 82, 70, 40],
        }
    )


class TestMLSpatial:
    def test_pca_to_3d_shape(self):
        import numpy as np

        matrix = np.random.randn(10, 5)
        coords, var, labels = pca_to_3d(matrix)
        assert coords.shape == (10, 3)
        assert len(labels) == 3

    def test_scan_feature_space(self):
        bundle = scan_results_to_feature_space(_sample_scan())
        assert len(bundle["tickers"]) == 4
        assert bundle["coords"].shape[0] == 4

    def test_opening_terrain_grid(self):
        xg, yg, zg, _ = build_opening_terrain(_sample_scan(), grid_n=10)
        assert xg.shape == (10, 10)
        assert zg.shape == (10, 10)

    def test_loss_landscape_finite(self):
        _, _, zg, *_ = synthetic_loss_landscape(n_grid=12)
        assert pytest.approx(float(zg.mean())) == float(zg.mean())
        assert not (zg != zg).any()
