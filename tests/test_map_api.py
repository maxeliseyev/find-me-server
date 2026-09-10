"""Выдача точек карты."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.enums import Species
from apps.pets.models import Pet
from apps.reports.models import LostReport, ReportStatus
from apps.sightings.models import Sighting, SightingSource, SightingStatus

pytestmark = pytest.mark.django_db

MOSCOW = Point(37.6173, 55.7558, srid=4326)
VIEWPORT = {"min_lon": 37.5, "min_lat": 55.6, "max_lon": 37.7, "max_lat": 55.9, "zoom": 22}


@pytest.fixture
def owner():
    return get_user_model().objects.create_user(username="owner", password="x")


@pytest.fixture
def report(owner):
    pet = Pet.objects.create(owner=owner, name="Рыжик", species=Species.CAT)
    return LostReport.objects.create(
        pet=pet,
        author=owner,
        last_seen_at=timezone.now() - timedelta(hours=2),
        last_seen_geog=MOSCOW,
    )


def get_map(**params):
    return APIClient().get(reverse("map-viewport"), {**VIEWPORT, **params})


def point_features(response):
    return [
        feature
        for feature in response.data["features"]
        if feature["properties"]["kind"] != "cluster"
    ]


def test_map_returns_active_report_at_public_location(report):
    response = get_map()

    assert response.status_code == 200
    assert response.data["type"] == "FeatureCollection"
    feature = next(
        item for item in point_features(response) if item["properties"]["kind"] == "report"
    )
    assert feature["properties"]["id"] == report.pk
    assert feature["properties"]["species"] == Species.CAT
    assert feature["geometry"]["coordinates"] != [MOSCOW.x, MOSCOW.y]
    assert "last_seen_geog" not in str(response.data)


def test_map_excludes_inactive_and_outside_reports(report):
    report.status = ReportStatus.ARCHIVED
    report.save(update_fields=["status"])
    outside_pet = Pet.objects.create(owner=report.author, species=Species.DOG)
    LostReport.objects.create(
        pet=outside_pet,
        author=report.author,
        last_seen_at=timezone.now(),
        last_seen_geog=Point(30, 60, srid=4326),
    )

    response = get_map()

    assert response.status_code == 200
    assert response.data["features"] == []


def test_map_returns_only_visible_sightings_in_bbox():
    visible = Sighting.objects.create(
        geog=MOSCOW,
        seen_at=timezone.now(),
        source=SightingSource.DEVICE_GPS,
        species=Species.CAT,
    )
    Sighting.objects.create(
        geog=MOSCOW,
        seen_at=timezone.now(),
        source=SightingSource.MANUAL_PIN,
        status=SightingStatus.HIDDEN,
    )
    Sighting.objects.create(
        geog=Point(30, 60, srid=4326),
        seen_at=timezone.now(),
        source=SightingSource.MANUAL_PIN,
    )

    response = get_map()

    assert response.status_code == 200
    features = point_features(response)
    assert [feature["properties"]["id"] for feature in features] == [visible.pk]
    assert "author" not in str(features)


def test_map_clusters_nearby_points_on_server():
    Sighting.objects.create(
        geog=MOSCOW,
        seen_at=timezone.now(),
        source=SightingSource.DEVICE_GPS,
    )
    Sighting.objects.create(
        geog=Point(37.61731, 55.75581, srid=4326),
        seen_at=timezone.now(),
        source=SightingSource.MANUAL_PIN,
    )

    response = get_map(zoom=10)

    assert response.status_code == 200
    assert response.data["features"] == [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": pytest.approx([37.617305, 55.755805])},
            "properties": {"kind": "cluster", "count": 2, "counts": {"reports": 0, "sightings": 2}},
        }
    ]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"min_lon": 37.7, "max_lon": 37.5},
        {"min_lat": 55.9, "max_lat": 55.6},
    ],
)
def test_map_rejects_missing_or_invalid_bbox(params):
    response = APIClient().get(reverse("map-viewport"), params)

    assert response.status_code == 400
