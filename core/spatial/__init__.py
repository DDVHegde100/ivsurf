"""3D vector and spatial geometry utilities."""

from core.spatial.geometry import (
    Vec3,
    angle_between,
    convex_hull_volume,
    cross,
    distance,
    dot,
    normalize,
    pairwise_distances,
    project_to_plane,
    rotation_matrix,
)

__all__ = [
    "Vec3",
    "dot",
    "cross",
    "distance",
    "normalize",
    "angle_between",
    "rotation_matrix",
    "project_to_plane",
    "pairwise_distances",
    "convex_hull_volume",
]
