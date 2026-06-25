"""3D neural network architecture layout."""

from __future__ import annotations

from dataclasses import dataclass

from core.spatial.geometry import Vec3


@dataclass
class LayerSpec:
    name: str
    units: int


def default_mlp_architecture() -> list[LayerSpec]:
    return [
        LayerSpec("Input", 8),
        LayerSpec("Dense+ReLU", 32),
        LayerSpec("Dropout", 32),
        LayerSpec("Dense+ReLU", 16),
        LayerSpec("Output", 1),
    ]


def layout_architecture_3d(
    layers: list[LayerSpec],
    *,
    layer_spacing: float = 2.5,
    unit_spacing: float = 0.35,
) -> tuple[list[Vec3], list[tuple[int, int]]]:
    """
    Place neurons on a 3D grid: x = layer index, y/z = unit grid.

    Returns node positions and edge list (from_idx, to_idx).
    """
    nodes: list[Vec3] = []
    edges: list[tuple[int, int]] = []
    layer_offsets: list[tuple[int, int]] = []

    for layer_idx, layer in enumerate(layers):
        count = min(layer.units, 12)  # cap visual density
        cols = int(count**0.5) + 1
        start = len(nodes)
        for i in range(count):
            row, col = divmod(i, cols)
            nodes.append(
                Vec3(
                    layer_idx * layer_spacing,
                    (col - cols / 2) * unit_spacing,
                    (row - cols / 2) * unit_spacing,
                )
            )
        layer_offsets.append((start, len(nodes)))

    for (a_start, a_end), (b_start, b_end) in zip(layer_offsets, layer_offsets[1:]):
        for i in range(a_start, a_end):
            for j in range(b_start, b_end):
                edges.append((i, j))

    return nodes, edges
