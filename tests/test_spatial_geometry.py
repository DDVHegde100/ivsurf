"""Tests for 3D geometry utilities."""

import math

import numpy as np
import pytest

from core.spatial.geometry import (
    Vec3,
    angle_between,
    convex_hull_volume,
    cross,
    distance,
    dot,
    normalize,
    rotation_matrix,
)


class TestGeometry:
    def test_dot_and_cross(self):
        a, b = Vec3(1, 0, 0), Vec3(0, 1, 0)
        assert dot(a, b) == 0.0
        c = cross(a, b)
        assert c.z == pytest.approx(1.0)

    def test_distance(self):
        assert distance(Vec3(0, 0, 0), Vec3(3, 4, 0)) == 5.0

    def test_normalize(self):
        n = normalize(Vec3(0, 0, 5))
        assert n.z == pytest.approx(1.0)

    def test_angle_between(self):
        assert angle_between(Vec3(1, 0, 0), Vec3(1, 0, 0)) == pytest.approx(0.0)
        assert angle_between(Vec3(1, 0, 0), Vec3(0, 1, 0)) == pytest.approx(math.pi / 2)

    def test_rotation_matrix_preserves_length(self):
        v = np.array([1.0, 2.0, 3.0])
        rot = rotation_matrix(Vec3(0, 0, 1), math.pi / 2)
        rotated = rot @ v
        assert np.linalg.norm(rotated) == pytest.approx(np.linalg.norm(v))

    def test_convex_hull_volume(self):
        pts = [
            Vec3(0, 0, 0),
            Vec3(1, 0, 0),
            Vec3(0, 1, 0),
            Vec3(0, 0, 1),
        ]
        vol = convex_hull_volume(pts)
        assert vol == pytest.approx(1 / 6, rel=0.05)
