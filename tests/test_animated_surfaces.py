"""Tests for animated surfaces."""

import numpy as np

from core.spatial.animated import sample_animation


class TestAnimatedSurfaces:
    def test_ripple_finite(self):
        xg, yg, zg = sample_animation("ripple", t=0.0, n=20)
        assert xg.shape == (20, 20)
        assert np.isfinite(zg).all()

    def test_all_animations(self):
        for name in ("ripple", "lissajous", "breathing_sphere"):
            xg, yg, zg = sample_animation(name, t=1.0, n=15)
            assert zg.shape == xg.shape
