"""Vector algebra and 3D spatial calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def as_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=float)

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def magnitude(self) -> float:
        return float(math.sqrt(self.x**2 + self.y**2 + self.z**2))


def dot(a: Vec3, b: Vec3) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def cross(a: Vec3, b: Vec3) -> Vec3:
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def distance(a: Vec3, b: Vec3) -> float:
    return (a - b).magnitude()


def normalize(v: Vec3) -> Vec3:
    mag = v.magnitude()
    if mag <= 0:
        return Vec3(0.0, 0.0, 0.0)
    return v * (1.0 / mag)


def angle_between(a: Vec3, b: Vec3) -> float:
    """Angle in radians between two vectors."""
    na, nb = normalize(a), normalize(b)
    cos_theta = max(-1.0, min(1.0, dot(na, nb)))
    return float(math.acos(cos_theta))


def rotation_matrix(axis: Vec3, angle_rad: float) -> np.ndarray:
    """Rodrigues rotation matrix for rotating around axis by angle."""
    k = normalize(axis).as_array()
    kx, ky, kz = k
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    t = 1 - c
    return np.array(
        [
            [t * kx * kx + c, t * kx * ky - s * kz, t * kx * kz + s * ky],
            [t * kx * ky + s * kz, t * ky * ky + c, t * ky * kz - s * kx],
            [t * kx * kz - s * ky, t * ky * kz + s * kx, t * kz * kz + c],
        ],
        dtype=float,
    )


def project_to_plane(point: Vec3, plane_normal: Vec3, plane_point: Vec3 | None = None) -> Vec3:
    """Orthogonal projection of a point onto a plane."""
    origin = plane_point or Vec3(0, 0, 0)
    n = normalize(plane_normal)
    v = point - origin
    dist = dot(v, n)
    projected = v - n * dist
    return origin + projected


def pairwise_distances(points: Sequence[Vec3]) -> np.ndarray:
    """NxN Euclidean distance matrix."""
    arr = np.array([p.as_array() for p in points], dtype=float)
    diff = arr[:, None, :] - arr[None, :, :]
    return np.sqrt((diff**2).sum(axis=2))


def convex_hull_volume(points: Iterable[Vec3]) -> float:
    """Volume of the 3D convex hull (requires scipy)."""
    from scipy.spatial import ConvexHull

    arr = np.array([p.as_array() for p in points], dtype=float)
    if arr.shape[0] < 4:
        return 0.0
    hull = ConvexHull(arr)
    return float(hull.volume)
