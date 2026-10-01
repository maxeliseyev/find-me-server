"""Приём и публикация фото отметок."""

import posixpath
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import signing
from django.core.files.storage import Storage
from django.db import transaction
from django.utils import timezone

from apps.core.enums import PhotoStatus
from apps.core.images import ImageProcessingError, extract_gps, sanitize_image

from .models import Sighting, SightingPhoto
from .tasks import process_sighting_photo

PHOTO_UPLOAD_SALT = "sightings.photo-upload"


class PhotoLimitReached(Exception):
    """У отметки уже максимум фото."""


def photo_upload_token(sighting: Sighting) -> str:
    """Подписанный токен, по которому автор отметки догружает к ней фото.

    Отметку ставят без регистрации (инвариант 1), поэтому «чья отметка» знает
    только тот, кто получил ответ на её создание. Токен живёт недолго: фото
    догружают сразу после отметки, а не через неделю.
    """
    return signing.dumps(sighting.pk, salt=PHOTO_UPLOAD_SALT)


def can_upload_photo(sighting: Sighting, user, token: str | None) -> bool:
    if user.is_authenticated and sighting.author_id == user.pk:
        return True
    if not token:
        return False
    try:
        sighting_id = signing.loads(
            token,
            salt=PHOTO_UPLOAD_SALT,
            max_age=settings.SIGHTING_PHOTO_UPLOAD_TTL_MINUTES * 60,
        )
    except signing.BadSignature:
        return False
    return sighting_id == sighting.pk


def accept_sighting_photo(sighting: Sighting, upload) -> SightingPhoto:
    """Положить исходник в карантин и поставить обработку в очередь.

    Декодирование — в Celery, не в запросе (инвариант 11). Здесь только дешёвые
    проверки размера и числа фото, чтобы не складывать в карантин лишнее.
    """
    if upload.size > settings.IMAGE_MAX_UPLOAD_BYTES:
        raise ImageProcessingError("Размер изображения превышает допустимый.")

    with transaction.atomic():
        # Блокировка отметки: параллельные загрузки не обходят лимит.
        Sighting.objects.select_for_update().filter(pk=sighting.pk).first()
        taken = sighting.photos.exclude(status=PhotoStatus.REJECTED).count()
        if taken >= settings.SIGHTING_PHOTOS_MAX:
            raise PhotoLimitReached

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


def _reject_abandoned_photo(photo_id: int) -> bool:
    """Отклонить фото, которое так и не удалось обработать, и убрать исходник."""
    with transaction.atomic():
        photo = (
            SightingPhoto.objects.select_for_update()
            .filter(pk=photo_id, status=PhotoStatus.PENDING)
            .first()
        )
        if photo is None:
            return False
        storage, name = photo.original.storage, photo.original.name
        photo.status = PhotoStatus.REJECTED
        photo.original = ""
        photo.save()
        if name:
            transaction.on_commit(lambda: storage.delete(name))
    return True


def _walk_files(storage: Storage, path: str = ""):
    directories, files = storage.listdir(path)
    for name in files:
        yield posixpath.join(path, name)
    for directory in directories:
        yield from _walk_files(storage, posixpath.join(path, directory))


def sweep_quarantine() -> dict[str, int]:
    """Довести до конца то, что обработка Celery оставила в карантине.

    Исходник с метаданными не должен лежать бесконечно (инвариант 4), а задача
    обработки может пропасть: упал брокер, воркер убит, storage ответил ошибкой.
    Идемпотентна: безопасно запускать параллельно с публикацией.
    """
    now = timezone.now()
    retry_before = now - timedelta(minutes=settings.SIGHTING_PHOTO_RETRY_AFTER_MINUTES)
    give_up_before = now - timedelta(hours=settings.SIGHTING_PHOTO_GIVE_UP_AFTER_HOURS)
    stats = {"requeued": 0, "rejected": 0, "orphans_deleted": 0}

    pending = SightingPhoto.objects.filter(status=PhotoStatus.PENDING, created_at__lt=retry_before)
    for photo_id, created_at in pending.values_list("pk", "created_at"):
        if created_at < give_up_before:
            stats["rejected"] += _reject_abandoned_photo(photo_id)
        else:
            process_sighting_photo.delay(photo_id)
            stats["requeued"] += 1

    # Файл пишется до строки в БД, поэтому свежие файлы без записи — не сироты,
    # а приём, который ещё не закоммитился.
    storage = SightingPhoto._meta.get_field("original").storage
    orphan_before = now - timedelta(hours=settings.QUARANTINE_ORPHAN_MIN_AGE_HOURS)
    referenced = set(SightingPhoto.objects.exclude(original="").values_list("original", flat=True))
    for name in _walk_files(storage):
        if name in referenced or storage.get_modified_time(name) >= orphan_before:
            continue
        storage.delete(name)
        stats["orphans_deleted"] += 1
    return stats
