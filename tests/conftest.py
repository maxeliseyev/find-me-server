import pytest
from django.contrib.gis.geos import Point


@pytest.fixture
def point() -> Point:
    """Точка в центре Москвы — дефолт для гео-тестов."""
    return Point(37.6173, 55.7558, srid=4326)


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Счётчики рейтлимита живут в кэше и протекают между тестами."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
