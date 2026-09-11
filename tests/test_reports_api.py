"""API создания объявлений о пропаже."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.enums import Sex, Size, Species
from apps.pets.models import Pet
from apps.reports.models import LocationPrecision, LostReport, ReportStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def owner():
    return get_user_model().objects.create_user(username="owner", password="x")


@pytest.fixture
def payload() -> dict:
    return {
        "pet": {
            "name": "Рыжик",
            "species": Species.CAT,
            "breed": "Европейская короткошёрстная",
            "colors": ["рыжий", "белый"],
            "size": Size.SMALL,
            "sex": Sex.MALE,
            "features": "Белая грудка",
            "chip_number": "123456",
        },
        "last_seen_at": (timezone.now() - timedelta(hours=2)).isoformat(),
        "lat": 55.7558,
        "lon": 37.6173,
        "search_radius_m": 1500,
        "reward_text": "Вознаграждение гарантировано",
    }


def test_authenticated_owner_creates_active_report_with_pet(client, owner, payload):
    client.force_authenticate(owner)

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 201
    report = LostReport.objects.get(pk=response.data["id"])
    assert report.author_id == owner.pk
    assert report.status == ReportStatus.ACTIVE
    assert report.location_precision == LocationPrecision.BLURRED
    assert (report.last_seen_geog.y, report.last_seen_geog.x) == (55.7558, 37.6173)
    assert report.pet.owner_id == owner.pk
    assert report.pet.colors == ["рыжий", "белый"]
    assert response.data["pet"]["chip_number"] == "123456"
    assert response.data["lat"] == pytest.approx(55.7558)


def test_anonymous_user_cannot_create_report(client, payload):
    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 403
    assert not Pet.objects.exists()
    assert not LostReport.objects.exists()


def test_banned_user_cannot_create_report(client, owner, payload):
    owner.is_banned = True
    owner.save(update_fields=["is_banned"])
    client.force_authenticate(owner)

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 403
    assert not LostReport.objects.exists()


def test_report_rejects_future_last_seen_at(client, owner, payload):
    client.force_authenticate(owner)
    payload["last_seen_at"] = (timezone.now() + timedelta(hours=1)).isoformat()

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 400
    assert "last_seen_at" in response.data
    assert not Pet.objects.exists()


def test_report_rejects_invalid_coordinates_without_creating_pet(client, owner, payload):
    client.force_authenticate(owner)
    payload["lat"] = 100

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 400
    assert "lat" in response.data
    assert not Pet.objects.exists()


def test_owner_can_explicitly_publish_exact_location(client, owner, payload):
    client.force_authenticate(owner)
    payload["location_precision"] = LocationPrecision.EXACT

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 201
    report = LostReport.objects.get(pk=response.data["id"])
    assert report.location_precision == LocationPrecision.EXACT
    assert report.public_geog.tuple == report.last_seen_geog.tuple


def test_report_response_never_includes_phone(client, owner, payload):
    client.force_authenticate(owner)

    response = client.post(reverse("report-create"), payload, format="json")

    assert response.status_code == 201
    assert "phone" not in str(response.data)
