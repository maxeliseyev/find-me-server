import math

import pytest
from django.contrib.gis.geos import Point

from apps.core.geo import blur_point


def _distance_m(a: Point, b: Point) -> float:
    d_lat = math.radians(b.y - a.y)
    d_lon = math.radians(b.x - a.x) * math.cos(math.radians(a.y))
    return 6_371_000 * math.hypot(d_lat, d_lon)


def test_blur_point_stays_within_radius(point):
    blurred = blur_point(point, radius_m=250)
    assert _distance_m(point, blurred) <= 250 + 1e-6


def test_blur_point_is_stable_for_same_seed(point):
    a = blur_point(point, radius_m=250, seed="report:1")
    b = blur_point(point, radius_m=250, seed="report:1")
    assert (a.x, a.y) == (b.x, b.y)


@pytest.mark.parametrize("seed", ["report:1", "report:2"])
def test_blur_point_moves_the_point(point, seed):
    assert blur_point(point, radius_m=250, seed=seed) != point
