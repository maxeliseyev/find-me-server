"""API постановки отметки (раздел 3.1 спеки)."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.enums import Species
from apps.pets.models import Pet
from apps.reports.models import LostReport, ReportStatus
from apps.sightings.models import Sighting, SightingSource, SightingStatus

pytestmark = pytest.mark.django_db

LAT, LON = 55.7558, 37.6173


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def payload() -> dict:
    return {
        "lat": LAT,
        "lon": LON,
        "seen_at": (timezone.now() - timedelta(hours=2)).isoformat(),
        "source": SightingSource.DEVICE_GPS,
        "species": Species.CAT,
        "comment": "Рыжий кот у пятого дома",
    }


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="volunteer", password="x")


@pytest.fixture
def active_report(user):
    pet = Pet.objects.create(owner=user, name="Рыжик", species=Species.CAT)
    return LostReport.objects.create(
        pet=pet,
        author=user,
        last_seen_at=timezone.now() - timedelta(days=1),
        last_seen_geog="POINT(37.6173 55.7558)",
    )


def test_anonymous_sighting_is_created(client, payload):
    response = client.post(reverse("sighting-create"), payload, format="json")

    assert response.status_code == 201
    sighting = Sighting.objects.get(pk=response.data["id"])
    assert sighting.author_id is None
    assert sighting.report_id is None
    assert (sighting.geog.y, sighting.geog.x) == (LAT, LON)


def test_authenticated_sighting_keeps_author(client, payload, user):
    client.force_authenticate(user)

    response = client.post(reverse("sighting-create"), payload, format="json")

    assert response.status_code == 201
    assert Sighting.objects.get(pk=response.data["id"]).author_id == user.pk


def test_sighting_can_be_attached_to_active_report(client, payload, active_report):
    response = client.post(
        reverse("sighting-create"), {**payload, "report": active_report.pk}, format="json"
    )

    assert response.status_code == 201
    assert Sighting.objects.get(pk=response.data["id"]).report_id == active_report.pk


def test_closed_report_does_not_accept_sightings(client, payload, active_report):
    active_report.status = ReportStatus.ARCHIVED
    active_report.save(update_fields=["status"])

    response = client.post(
        reverse("sighting-create"), {**payload, "report": active_report.pk}, format="json"
    )

    assert response.status_code == 400
    assert "report" in response.data


def test_future_sighting_is_rejected(client, payload):
    payload["seen_at"] = (timezone.now() + timedelta(hours=3)).isoformat()

    response = client.post(reverse("sighting-create"), payload, format="json")

    assert response.status_code == 400
    assert "seen_at" in response.data


def test_coordinates_are_validated(client, payload):
    response = client.post(reverse("sighting-create"), {**payload, "lat": 120}, format="json")

    assert response.status_code == 400
    assert "lat" in response.data


def test_banned_user_cannot_post(client, payload, user):
    user.is_banned = True
    user.save(update_fields=["is_banned"])
    client.force_authenticate(user)

    response = client.post(reverse("sighting-create"), payload, format="json")

    assert response.status_code == 403
    assert not Sighting.objects.exists()


def test_response_does_not_leak_author(client, payload, user):
    client.force_authenticate(user)

    response = client.post(reverse("sighting-create"), payload, format="json")

    assert "author" not in response.data
    assert "volunteer" not in str(response.data)


def test_hidden_sighting_is_not_served(client, payload):
    created = client.post(reverse("sighting-create"), payload, format="json")
    sighting = Sighting.objects.get(pk=created.data["id"])
    sighting.status = SightingStatus.HIDDEN
    sighting.save(update_fields=["status"])

    response = client.get(reverse("sighting-detail", args=[sighting.pk]))

    assert response.status_code == 404


def test_visible_sighting_is_served(client, payload):
    created = client.post(reverse("sighting-create"), payload, format="json")

    response = client.get(reverse("sighting-detail", args=[created.data["id"]]))

    assert response.status_code == 200
    assert response.data["lat"] == pytest.approx(LAT)
    assert response.data["comment"] == "Рыжий кот у пятого дома"
