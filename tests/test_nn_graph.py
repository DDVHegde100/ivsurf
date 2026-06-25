"""Tests for 3D NN architecture layout."""

from engine.spatial.nn_graph import default_mlp_architecture, layout_architecture_3d


class TestNNGraph:
    def test_layout_produces_edges(self):
        layers = default_mlp_architecture()
        nodes, edges = layout_architecture_3d(layers)
        assert len(nodes) > 0
        assert len(edges) > 0

    def test_edges_connect_layers(self):
        layers = default_mlp_architecture()
        nodes, edges = layout_architecture_3d(layers)
        assert all(0 <= a < len(nodes) and 0 <= b < len(nodes) for a, b in edges)
