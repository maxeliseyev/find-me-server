"""API загрузки фото к отметке."""

from datetime import timedelta
from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.core.enums import PhotoStatus
from apps.sightings.models import Sighting, SightingPhoto, SightingSource, SightingStatus

pytestmark = pytest.mark.django_db


def jpeg() -> SimpleUploadedFile:
    raw = BytesIO()
    Image.new("RGB", (20, 10), "orange").save(raw, "JPEG")
    return SimpleUploadedFile("photo.jpg", raw.getvalue(), content_type="image/jpeg")


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def created(client) -> dict:
    """Ответ на создание анонимной отметки — в нём токен загрузки фото."""
    response = client.post(
        reverse("sighting-create"),
        {
            "lat": 55.7558,
            "lon": 37.6173,
            "seen_at": (timezone.now() - timedelta(minutes=10)).isoformat(),
            "source": SightingSource.DEVICE_GPS,
        },
        format="json",
    )
    assert response.status_code == 201
    return response.data


def upload(client, sighting_id, **data):
    return client.post(
        reverse("sighting-photo-upload", args=[sighting_id]),
        {"image": jpeg(), **data},
        format="multipart",
    )


def test_create_response_carries_upload_token_but_detail_does_not(client, created):
    assert created["photo_upload_token"]

    detail = client.get(reverse("sighting-detail", args=[created["id"]]))

    assert "photo_upload_token" not in detail.data


def test_anonymous_author_uploads_photo_with_token(
    client, created, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = upload(client, created["id"], upload_token=created["photo_upload_token"])

    assert response.status_code == 202
    assert response.data["status"] == PhotoStatus.PENDING
    assert response.data["url"] is None

    detail = client.get(reverse("sighting-detail", args=[created["id"]]))
    [photo] = detail.data["photos"]
    assert photo["status"] == PhotoStatus.PUBLISHED
    assert photo["url"].endswith(".webp")


def test_upload_without_token_is_forbidden(client, created):
    response = upload(client, created["id"])

    assert response.status_code == 403
    assert not SightingPhoto.objects.exists()


def test_token_of_another_sighting_is_forbidden(client, created):
    other = Sighting.objects.create(
        geog="POINT(37.6 55.7)", seen_at=timezone.now(), source=SightingSource.MANUAL_PIN
    )

    response = upload(client, other.pk, upload_token=created["photo_upload_token"])

    assert response.status_code == 403


def test_expired_token_is_forbidden(client, created, settings):
    settings.SIGHTING_PHOTO_UPLOAD_TTL_MINUTES = -1

    response = upload(client, created["id"], upload_token=created["photo_upload_token"])

    assert response.status_code == 403


def test_authenticated_author_uploads_without_token():
    user = get_user_model().objects.create_user(username="witness", password="x")
    sighting = Sighting.objects.create(
        geog="POINT(37.6 55.7)",
        seen_at=timezone.now(),
        source=SightingSource.MANUAL_PIN,
        author=user,
    )
    client = APIClient()
    client.force_authenticate(user)

    assert upload(client, sighting.pk).status_code == 202


def test_hidden_sighting_does_not_accept_photos(client, created):
    Sighting.objects.filter(pk=created["id"]).update(status=SightingStatus.HIDDEN)

    response = upload(client, created["id"], upload_token=created["photo_upload_token"])

    assert response.status_code == 404


def test_photo_limit_per_sighting(client, created, settings):
    settings.SIGHTING_PHOTOS_MAX = 1
    token = created["photo_upload_token"]

    assert upload(client, created["id"], upload_token=token).status_code == 202
    response = upload(client, created["id"], upload_token=token)

    assert response.status_code == 400
    assert SightingPhoto.objects.count() == 1


def test_oversized_upload_is_rejected(client, created, settings):
    settings.IMAGE_MAX_UPLOAD_BYTES = 10

    response = upload(client, created["id"], upload_token=created["photo_upload_token"])

    assert response.status_code == 400
    assert "image" in response.data


def test_file_is_not_decoded_in_request(client, created, django_capture_on_commit_callbacks):
    """Не-изображение принимается в карантин и отклоняется уже Celery (инвариант 11)."""
    fake = SimpleUploadedFile("photo.jpg", b"not an image", content_type="image/jpeg")

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("sighting-photo-upload", args=[created["id"]]),
            {"image": fake, "upload_token": created["photo_upload_token"]},
            format="multipart",
        )

    assert response.status_code == 202
    assert SightingPhoto.objects.get().status == PhotoStatus.REJECTED
