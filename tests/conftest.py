import pytest
from django.contrib.gis.geos import Point


@pytest.fixture
def point() -> Point:
    """Точка в центре Москвы — дефолт для гео-тестов."""
    return Point(37.6173, 55.7558, srid=4326)
