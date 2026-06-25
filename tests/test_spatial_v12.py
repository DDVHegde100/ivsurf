"""Tests for v1.2 spatial analytics modules."""

import numpy as np
import pytest

from engine.spatial.monte_carlo_paths import simulate_gbm_paths
from engine.spatial.risk_ellipsoid import covariance_ellipsoid_mesh, sample_portfolio_covariance
from engine.spatial.spectral import fourier_amplitude_surface
from visuals.plot_3d.export import export_figure_html
from visuals.plot_3d.price_paths import synthetic_price_path


class TestSpatialV12:
    def test_risk_ellipsoid_mesh(self):
        cov = sample_portfolio_covariance()
        xg, yg, zg = covariance_ellipsoid_mesh(cov)
        assert xg.shape == yg.shape == zg.shape

    def test_spectral_surface(self):
        series = np.cumsum(np.random.randn(200))
        tg, fg, amp = fourier_amplitude_surface(series, n_time=30, n_freq=32)
        assert amp.shape == tg.shape

    def test_gbm_paths(self):
        times, paths, terminal = simulate_gbm_paths(n_paths=5, n_steps=50)
        assert paths.shape == (5, 50)
        assert len(times) == 50

    def test_price_path_synthetic(self):
        df = synthetic_price_path(30)
        assert len(df) == 30

    def test_export_html(self, tmp_path):
        import plotly.graph_objects as go

        fig = go.Figure(data=[go.Scatter3d(x=[0], y=[0], z=[0])])
        out = export_figure_html(fig, tmp_path / "test.html")
        assert out.exists()
        assert "html" in out.read_text()[:20].lower() or "<" in out.read_text()
