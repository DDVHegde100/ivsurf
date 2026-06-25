"""Tests for parametric surfaces."""

import numpy as np

from core.spatial.parametric import get_surface, list_surfaces, sample_surface


class TestParametricSurfaces:
    def test_catalog_not_empty(self):
        assert len(list_surfaces()) >= 5

    def test_sphere_sampling(self):
        surf = get_surface("sphere")
        xg, yg, zg = sample_surface(surf, n=20)
        radii = np.sqrt(xg**2 + yg**2 + zg**2)
        assert np.allclose(radii, 1.0, atol=0.05)

    def test_saddle_has_negative_and_positive_z(self):
        surf = get_surface("saddle")
        _, _, zg = sample_surface(surf, n=30)
        assert zg.min() < 0
        assert zg.max() > 0
