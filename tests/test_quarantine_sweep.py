"""Уборка карантина фото: зависшие обработки и файлы-сироты."""

from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image

from apps.core.enums import PhotoStatus
from apps.core.storage import quarantine_storage
from apps.sightings.models import Sighting, SightingPhoto, SightingSource
from apps.sightings.services import sweep_photo_quarantine

pytestmark = pytest.mark.django_db


def jpeg_bytes() -> bytes:
    raw = BytesIO()
    Image.new("RGB", (20, 10), "orange").save(raw, "JPEG")
    return raw.getvalue()


@pytest.fixture
def sighting(point):
    return Sighting.objects.create(
        geog=point, seen_at=timezone.now(), source=SightingSource.MANUAL_PIN
    )


@pytest.fixture
def pending_photo(sighting):
    """Фото, чья задача обработки потерялась: исходник в карантине, статус pending."""
    photo = SightingPhoto(sighting=sighting)
    photo.original.save("stuck", ContentFile(jpeg_bytes()), save=False)
    photo.save()
    return photo


def later(**delta):
    return timezone.now() + timedelta(**delta)


def test_fresh_pending_photo_is_left_alone(pending_photo):
    with patch("apps.sightings.services.process_sighting_photo") as task:
        result = sweep_photo_quarantine(now=later(minutes=5))

    task.delay.assert_not_called()
    assert result.retried == 0
    pending_photo.refresh_from_db()
    assert pending_photo.status == PhotoStatus.PENDING


def test_stuck_pending_photo_is_processed_again(pending_photo, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        result = sweep_photo_quarantine(now=later(minutes=30))

    assert result.retried == 1
    pending_photo.refresh_from_db()
    assert pending_photo.status == PhotoStatus.PUBLISHED


def test_hopeless_pending_photo_is_rejected_and_original_deleted(
    pending_photo, django_capture_on_commit_callbacks
):
    name = pending_photo.original.name

    with (
        patch("apps.sightings.services.process_sighting_photo") as task,
        django_capture_on_commit_callbacks(execute=True),
    ):
        result = sweep_photo_quarantine(now=later(hours=25))

    task.delay.assert_not_called()
    assert result.given_up == 1
    pending_photo.refresh_from_db()
    assert pending_photo.status == PhotoStatus.REJECTED
    assert not pending_photo.original
    assert not quarantine_storage().exists(name)


def test_old_orphan_is_deleted_but_referenced_and_fresh_files_stay(pending_photo):
    storage = quarantine_storage()
    orphan = storage.save("sightings/2026/09/orphan", ContentFile(b"raw"))

    with patch("apps.sightings.services.process_sighting_photo"):
        stale = sweep_photo_quarantine(now=later(hours=2))

    assert stale.orphans_deleted >= 1
    assert not storage.exists(orphan)
    assert storage.exists(pending_photo.original.name)


def test_orphan_within_grace_period_survives():
    storage = quarantine_storage()
    upload_in_flight = storage.save("sightings/2026/09/in-flight", ContentFile(b"raw"))

    sweep_photo_quarantine(now=later(minutes=10))

    assert storage.exists(upload_in_flight)
    storage.delete(upload_in_flight)
