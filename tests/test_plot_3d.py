"""Tests for 3D plot helpers."""

import numpy as np

from visuals.plot_3d.base import figure_3d, grid_from_function, surface_from_grid


class TestPlot3DBase:
    def test_grid_from_function(self):
        xg, yg, zg = grid_from_function(lambda x, y: x**2 + y**2, (-1, 1), (-1, 1), n=10)
        assert xg.shape == (10, 10)
        assert zg.min() >= 0.0

    def test_figure_3d_builds(self):
        fig = figure_3d("Test")
        assert fig.layout.scene is not None

    def test_surface_trace(self):
        xg, yg, zg = grid_from_function(lambda x, y: np.sin(x) * np.cos(y), (-3, 3), (-3, 3), n=5)
        trace = surface_from_grid(xg, yg, zg)
        assert trace.type == "surface"
