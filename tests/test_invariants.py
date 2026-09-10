"""Инварианты `AGENTS.md` как исполняемый контракт.

Имя теста ссылается на номер инварианта. Текст, который можно прочитать
невнимательно, так превращается в факт, который падает.

Инвариант, поведения для которого ещё нет (фан-аут, EXIF, веса), получает
тест вместе с реализацией — в том же PR.
"""

import math
from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.enums import Species
from apps.geo.models import GeoSubscription
from apps.pets.models import Pet
from apps.reports.models import LocationPrecision, LostReport
from apps.sightings.models import Sighting, SightingSource

MOSCOW = Point(37.6173, 55.7558, srid=4326)


def distance_m(a: Point, b: Point) -> float:
    d_lat = math.radians(b.y - a.y)
    d_lon = math.radians(b.x - a.x) * math.cos(math.radians(a.y))
    return 6_371_000 * math.hypot(d_lat, d_lon)


@pytest.fixture
def owner(db):
    return get_user_model().objects.create_user(username="owner", password="x")


@pytest.fixture
def report(db, owner):
    pet = Pet.objects.create(owner=owner, name="Рыжик", species=Species.CAT)
    return LostReport.objects.create(
        pet=pet,
        author=owner,
        last_seen_at=timezone.now() - timedelta(hours=5),
        last_seen_geog=MOSCOW,
    )


@pytest.mark.django_db
def test_invariant_01_sighting_is_saved_without_author_and_report():
    """До отправки отметки — ноль экранов регистрации, привязка необязательна."""
    sighting = Sighting.objects.create(
        geog=MOSCOW,
        seen_at=timezone.now(),
        source=SightingSource.DEVICE_GPS,
        species=Species.CAT,
    )

    sighting.refresh_from_db()
    assert sighting.pk is not None
    assert sighting.author_id is None
    assert sighting.report_id is None


@pytest.mark.django_db
def test_invariant_02_unidentified_sighting_outlives_its_report(report):
    """Неопознанная отметка живёт сама по себе: объявление ушло — данные остались."""
    sighting = Sighting.objects.create(
        report=report,
        geog=MOSCOW,
        seen_at=timezone.now(),
        source=SightingSource.MANUAL_PIN,
    )

    report.delete()

    sighting.refresh_from_db()
    assert sighting.report_id is None


@pytest.mark.django_db
def test_invariant_03_public_geog_hides_the_exact_point(report):
    """Публично отдаётся смещённая точка, и смещение не выходит за радиус."""
    public = report.public_geog

    assert (public.x, public.y) != (report.last_seen_geog.x, report.last_seen_geog.y)
    assert distance_m(report.last_seen_geog, public) <= settings.PUBLIC_LOCATION_BLUR_M


@pytest.mark.django_db
def test_invariant_03_blur_is_stable_between_calls(report):
    """Смещение детерминировано: случайное на каждый запрос усредняется в исходное."""
    first, second = report.public_geog, report.public_geog

    assert (first.x, first.y) == (second.x, second.y)


@pytest.mark.django_db
def test_invariant_03_exact_precision_is_owners_explicit_choice(report):
    report.location_precision = LocationPrecision.EXACT
    report.save(update_fields=["location_precision"])

    assert report.public_geog.tuple == report.last_seen_geog.tuple


@pytest.mark.django_db
def test_invariant_06_geo_fields_are_geography_with_gist_index():
    """Координаты — geography(Point,4326); поиск по радиусу идёт по GiST."""
    fields = [
        Sighting._meta.get_field("geog"),
        LostReport._meta.get_field("last_seen_geog"),
        GeoSubscription._meta.get_field("geog"),
    ]
    for field in fields:
        assert field.geography is True, field
        assert field.srid == 4326, field

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_indexes "
            "WHERE indexdef ILIKE '%%USING gist%%' AND schemaname = 'public'"
        )
        tables = {row[0] for row in cursor.fetchall()}

    assert {"sightings_sighting", "reports_lostreport", "geo_geosubscription"} <= tables


@pytest.mark.django_db
def test_invariant_07_seen_at_is_independent_from_created_at():
    """Человек ставит отметку о вчерашнем наблюдении; вес считается по seen_at."""
    yesterday = timezone.now() - timedelta(days=1)
    sighting = Sighting.objects.create(
        geog=MOSCOW, seen_at=yesterday, source=SightingSource.MANUAL_PIN
    )

    sighting.refresh_from_db()
    assert sighting.seen_at < sighting.created_at
    assert timezone.is_aware(sighting.seen_at)
    assert settings.USE_TZ is True


@pytest.mark.django_db
def test_invariant_01_api_accepts_sighting_without_any_auth():
    """Ноль экранов регистрации до отправки: анонимный POST обязан сохранять."""
    response = APIClient().post(
        reverse("sighting-create"),
        {
            "lat": MOSCOW.y,
            "lon": MOSCOW.x,
            "seen_at": (timezone.now() - timedelta(hours=1)).isoformat(),
            "source": SightingSource.DEVICE_GPS,
        },
        format="json",
    )

    assert response.status_code == 201
    assert Sighting.objects.get(pk=response.data["id"]).author_id is None


@pytest.mark.django_db
def test_invariant_12_anonymous_sightings_are_rate_limited():
    """Для неавторизованного действия рейтлимит — единственная защита."""
    client = APIClient()
    url = reverse("sighting-create")
    limit = int(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon_sighting"].split("/")[0])

    def post():
        return client.post(
            url,
            {
                "lat": MOSCOW.y,
                "lon": MOSCOW.x,
                "seen_at": (timezone.now() - timedelta(minutes=5)).isoformat(),
                "source": SightingSource.MANUAL_PIN,
            },
            format="json",
        )

    for _ in range(limit):
        assert post().status_code == 201

    assert post().status_code == 429
