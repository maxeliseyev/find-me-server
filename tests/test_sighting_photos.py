"""Карантин и Celery-публикация фото отметок."""

from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from apps.core.enums import PhotoStatus
from apps.core.images import ImageProcessingError
from apps.sightings.models import Sighting, SightingPhoto, SightingSource
from apps.sightings.services import (
    accept_sighting_photo,
    publish_sighting_photo,
    sweep_quarantine,
)

GPS = {1: "N", 2: (55, 45, 30), 3: "E", 4: (37, 36, 15)}


def jpeg(*, gps=None, name="подъезд-5.jpg") -> SimpleUploadedFile:
    exif = Image.Exif()
    if gps:
        exif[34853] = gps
    raw = BytesIO()
    Image.new("RGB", (20, 10), "orange").save(raw, "JPEG", exif=exif)
    return SimpleUploadedFile(name, raw.getvalue(), content_type="image/jpeg")


@pytest.fixture
def sighting(db, point):
    return Sighting.objects.create(
        geog=point, seen_at=timezone.now(), source=SightingSource.MANUAL_PIN
    )


def test_accepted_photo_waits_in_quarantine_under_random_name(
    sighting, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks() as callbacks:
        photo = accept_sighting_photo(sighting, jpeg())

    photo.refresh_from_db()
    assert photo.status == PhotoStatus.PENDING
    assert not photo.image
    assert storages["quarantine"].exists(photo.original.name)
    assert "подъезд" not in photo.original.name
    assert len(callbacks) == 1


def test_published_photo_keeps_gps_privately_and_drops_original(
    sighting, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        photo = accept_sighting_photo(sighting, jpeg(gps=GPS))
    original_name = photo.original.name

    photo.refresh_from_db()
    assert photo.status == PhotoStatus.PUBLISHED
    assert photo.exif_stripped is True
    assert photo.image.name.endswith(".webp")
    assert len(photo.sha256) == 64
    assert photo.exif_geog.x == pytest.approx(37.6041667)
    assert photo.exif_geog.y == pytest.approx(55.7583333)
    assert not photo.original
    assert not storages["quarantine"].exists(original_name)


def test_non_image_is_rejected_and_removed_from_quarantine(
    sighting, django_capture_on_commit_callbacks
):
    fake = SimpleUploadedFile("photo.jpg", b"<?php echo 1; ?>", content_type="image/jpeg")
    with django_capture_on_commit_callbacks(execute=True):
        photo = accept_sighting_photo(sighting, fake)
    original_name = photo.original.name

    photo.refresh_from_db()
    assert photo.status == PhotoStatus.REJECTED
    assert not photo.image
    assert not storages["quarantine"].exists(original_name)


def test_publishing_twice_is_a_no_op(sighting, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        photo = accept_sighting_photo(sighting, jpeg())
    photo.refresh_from_db()
    published_name = photo.image.name

    with django_capture_on_commit_callbacks(execute=True):
        assert publish_sighting_photo(photo.pk) is None

    photo.refresh_from_db()
    assert photo.image.name == published_name


def test_oversized_upload_never_reaches_quarantine(sighting, settings):
    settings.IMAGE_MAX_UPLOAD_BYTES = 10

    with pytest.raises(ImageProcessingError, match="Размер"):
        accept_sighting_photo(sighting, jpeg())

    assert not SightingPhoto.objects.exists()


def test_photo_without_original_is_rejected(sighting):
    photo = SightingPhoto.objects.create(sighting=sighting)

    assert publish_sighting_photo(photo.pk) == PhotoStatus.REJECTED


# --- уборка карантина -------------------------------------------------------


def later(**delta):
    """Подменить «сейчас» в сервисе: файлы и записи при этом остаются «свежими»."""
    return patch(
        "apps.sightings.services.timezone.now", return_value=timezone.now() + timedelta(**delta)
    )


@pytest.fixture
def pending_photo(sighting):
    """Фото, которое приняли, но обработка так и не отработала."""
    with patch("apps.sightings.services.process_sighting_photo"):
        return accept_sighting_photo(sighting, jpeg())


def test_sweep_leaves_fresh_pending_photo_alone(pending_photo):
    with patch("apps.sightings.services.process_sighting_photo") as task:
        stats = sweep_quarantine()

    task.delay.assert_not_called()
    assert stats == {"requeued": 0, "rejected": 0, "orphans_deleted": 0}


def test_sweep_requeues_stuck_pending_photo(pending_photo):
    with (
        later(minutes=settings.SIGHTING_PHOTO_RETRY_AFTER_MINUTES + 1),
        patch("apps.sightings.services.process_sighting_photo") as task,
    ):
        stats = sweep_quarantine()

    task.delay.assert_called_once_with(pending_photo.pk)
    assert stats["requeued"] == 1
    assert storages["quarantine"].exists(pending_photo.original.name)


def test_sweep_rejects_abandoned_photo_and_deletes_original(
    pending_photo, django_capture_on_commit_callbacks
):
    name = pending_photo.original.name

    with (
        later(hours=settings.SIGHTING_PHOTO_GIVE_UP_AFTER_HOURS + 1),
        patch("apps.sightings.services.process_sighting_photo") as task,
        django_capture_on_commit_callbacks(execute=True),
    ):
        stats = sweep_quarantine()

    task.delay.assert_not_called()
    pending_photo.refresh_from_db()
    assert stats["rejected"] == 1
    assert pending_photo.status == PhotoStatus.REJECTED
    assert not pending_photo.original
    assert not storages["quarantine"].exists(name)


def test_sweep_deletes_old_orphan_but_keeps_referenced_and_fresh_files(pending_photo, settings):
    settings.SIGHTING_PHOTO_GIVE_UP_AFTER_HOURS = 1000  # фото не должно быть отклонено
    storage = storages["quarantine"]
    orphan = storage.save("sightings/2026/09/orphan", ContentFile(b"x"))

    with patch("apps.sightings.services.process_sighting_photo"):
        stats = sweep_quarantine()
    assert storage.exists(orphan), "свежий файл без записи — это приём в процессе"

    with (
        later(hours=settings.QUARANTINE_ORPHAN_MIN_AGE_HOURS + 1),
        patch("apps.sightings.services.process_sighting_photo"),
    ):
        stats = sweep_quarantine()

    assert not storage.exists(orphan)
    assert storage.exists(pending_photo.original.name), "исходник с записью не трогаем"
    assert stats["orphans_deleted"] == 1
