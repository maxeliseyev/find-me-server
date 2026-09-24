"""Приём и публикация фото отметок."""

from uuid import uuid4

from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction

from apps.core.enums import PhotoStatus
from apps.core.images import ImageProcessingError, extract_gps, sanitize_image

from .models import Sighting, SightingPhoto
from .tasks import process_sighting_photo


def accept_sighting_photo(sighting: Sighting, upload) -> SightingPhoto:
    """Положить исходник в карантин и поставить обработку в очередь.

    Декодирование — в Celery, не в запросе (инвариант 11). Здесь только дешёвая
    проверка размера, чтобы не складывать в карантин заведомо лишнее.
    """
    if upload.size > settings.IMAGE_MAX_UPLOAD_BYTES:
        raise ImageProcessingError("Размер изображения превышает допустимый.")

    photo = SightingPhoto(sighting=sighting)
    # Имя файла от пользователя не сохраняем: «подъезд_5_мой_дом.jpg» — тоже данные.
    photo.original.save(uuid4().hex, upload, save=False)
    photo.save()
    transaction.on_commit(lambda: process_sighting_photo.delay(photo.pk))
    return photo


def publish_sighting_photo(photo_id: int) -> PhotoStatus | None:
    """Перекодировать исходник в публичную копию и удалить его из карантина.

    Идемпотентна: повторный запуск задачи по уже обработанному фото ничего не
    делает. Возвращает итоговый статус или None, если обрабатывать нечего.
    """
    with transaction.atomic():
        photo = (
            SightingPhoto.objects.select_for_update()
            .filter(pk=photo_id, status=PhotoStatus.PENDING)
            .first()
        )
        if photo is None:
            return None

        original = photo.original
        if not original:
            # Записи до карантина: исходника нет, проверить копию нечем.
            photo.status = PhotoStatus.REJECTED
            photo.save(update_fields=["status", "updated_at"])
            return photo.status

        try:
            with original.open("rb") as source:
                gps = extract_gps(source)
                sanitized = sanitize_image(source)
        except ImageProcessingError:
            photo.status = PhotoStatus.REJECTED
        else:
            photo.image.save(sanitized.content.name, sanitized.content, save=False)
            photo.sha256 = sanitized.sha256
            photo.exif_geog = Point(*gps, srid=4326) if gps else None
            photo.exif_stripped = True
            photo.status = PhotoStatus.PUBLISHED

        # Исходник удаляем после коммита: откат транзакции не должен оставить
        # фото в статусе «ожидает» без файла, который можно переобработать.
        storage, name = original.storage, original.name
        photo.original = ""
        photo.save()
        transaction.on_commit(lambda: storage.delete(name))

    return photo.status
