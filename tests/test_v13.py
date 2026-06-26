"""Tests for v1.3 spatial modules and Vercel config."""

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestVercelConfig:
    def test_vercel_json_points_to_api_index(self):
        text = (ROOT / "vercel.json").read_text()
        assert "api/index.py" in text

    def test_public_landing_exists(self):
        assert (ROOT / "public" / "index.html").exists()
        assert "OpenPulse" in (ROOT / "public" / "index.html").read_text()

    def test_api_index_exports_app(self):
        from api.index import app

        assert app.title


class TestV13Spatial:
    def test_heston_surface(self):
        from engine.spatial.heston_surface import heston_iv_surface

        kg, eg, iv = heston_iv_surface()
        assert iv.shape == kg.shape

    def test_training_history(self):
        from engine.spatial.training_history import synthetic_training_history, training_history_to_3d_grid

        hist = synthetic_training_history(20)
        eg, mg, zg = training_history_to_3d_grid(hist)
        assert zg.shape == eg.shape

    def test_regime_layout(self):
        from engine.spatial.regime_graph import default_transition_matrix, regime_transition_layout

        xs, ys, zs, labels = regime_transition_layout(default_transition_matrix())
        assert len(xs) == 3

    def test_jacobian(self):
        from core.spatial.vector_field import numerical_jacobian

        jac = numerical_jacobian(lambda p: np.array([p[0] ** 2, p[1], p[2]]), np.array([1.0, 2.0, 3.0]))
        assert jac.shape == (3, 3)

    def test_spatial_api_catalog(self):
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
        resp = client.get("/spatial/catalog")
        assert resp.status_code == 200
        assert "surfaces" in resp.json()
