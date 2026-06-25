"""Tests for 3D knowledge graph layout."""

from engine.spatial.knowledge_graph import (
    build_knowledge_edges,
    build_sector_map,
    spring_layout_3d,
)


class TestKnowledgeGraph:
    def test_sector_map_assigns_preset(self):
        sector_map = build_sector_map(["AAPL", "NVDA", "UNKNOWN"])
        assert sector_map["AAPL"] in {"tech_mega", "core", "opening", "etfs", "high_beta"}
        assert sector_map["UNKNOWN"] == "other"

    def test_edges_within_sector(self):
        tickers = ["AAPL", "MSFT", "XOM"]
        sectors = {"AAPL": "tech", "MSFT": "tech", "XOM": "energy"}
        edges = build_knowledge_edges(tickers, sectors)
        assert ("AAPL", "MSFT", 1.0) in edges
        assert not any(a == "XOM" and b == "AAPL" for a, b, _ in edges)

    def test_spring_layout_returns_all_tickers(self):
        tickers = ["A", "B", "C", "D"]
        edges = [("A", "B", 1.0), ("C", "D", 1.0)]
        layout = spring_layout_3d(tickers, edges, iterations=30)
        assert set(layout.keys()) == set(tickers)
