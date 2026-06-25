"""Tests for 3D correlation layout."""

from engine.spatial.correlation_layout import correlation_from_sectors, embed_correlation_3d, layout_tickers_3d


class TestCorrelationLayout:
    def test_sector_correlation_higher_within_sector(self):
        tickers = ["AAPL", "MSFT", "XOM"]
        sectors = {"AAPL": "tech", "MSFT": "tech", "XOM": "energy"}
        corr = correlation_from_sectors(tickers, sectors)
        assert corr[0, 1] > corr[0, 2]

    def test_embed_produces_3d_coords(self):
        tickers = ["A", "B", "C", "D"]
        sectors = {"A": "x", "B": "x", "C": "y", "D": "y"}
        layout = layout_tickers_3d(tickers, sectors)
        assert set(layout.keys()) == set(tickers)
        for coords in layout.values():
            assert len(coords) == 3

    def test_mds_output_shape(self):
        import numpy as np

        corr = np.array([[1, 0.5, 0.2], [0.5, 1, 0.3], [0.2, 0.3, 1]], dtype=float)
        coords = embed_correlation_3d(corr)
        assert coords.shape == (3, 3)
