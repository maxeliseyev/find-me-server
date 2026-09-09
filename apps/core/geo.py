"""Гео-утилиты.

Раздел 9 спеки: точка пропажи — обычно подъезд владельца. Публично отдаём
смещённую точку, точную — только в чате по решению владельца.
"""

import math
import random

from django.conf import settings
from django.contrib.gis.geos import Point

EARTH_RADIUS_M = 6_371_000


def blur_point(point: Point, radius_m: int | None = None, *, seed: str | None = None) -> Point:
    """Сместить точку на случайный вектор внутри круга радиуса `radius_m`.

    `seed` фиксирует смещение для конкретного объекта: без него точку можно
    усреднить по нескольким запросам и восстановить исходную.
    """
    radius_m = radius_m or settings.PUBLIC_LOCATION_BLUR_M
    rnd = random.Random(seed) if seed else random.SystemRandom()

    distance = radius_m * math.sqrt(rnd.random())
    bearing = rnd.uniform(0, 2 * math.pi)

    d_lat = (distance * math.cos(bearing)) / EARTH_RADIUS_M
    d_lon = (distance * math.sin(bearing)) / (EARTH_RADIUS_M * math.cos(math.radians(point.y)))

    return Point(
        point.x + math.degrees(d_lon),
        point.y + math.degrees(d_lat),
        srid=point.srid or 4326,
    )
