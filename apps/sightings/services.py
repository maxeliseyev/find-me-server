"""Приём и публикация фото отметок."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core import signing
from django.db import transaction
from django.utils import timezone

from apps.core.enums import PhotoStatus
from apps.core.images import ImageProcessingError, extract_gps, sanitize_image
from apps.core.storage import quarantine_storage, walk_files

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


@dataclass(frozen=True)
class QuarantineSweep:
    retried: int
    given_up: int
    orphans_deleted: int


def sweep_photo_quarantine(now: datetime | None = None) -> QuarantineSweep:
    """Довести или отбросить зависшие фото и удалить файлы-сироты из карантина.

    Исходник с EXIF не должен жить в карантине дольше, чем его обрабатывают:
    задача могла упасть на сбое storage, воркер — перезапуститься, транзакция
    приёма — откатиться после записи файла.
    """
    now = now or timezone.now()
    pending = SightingPhoto.objects.filter(status=PhotoStatus.PENDING)

    give_up_before = now - timedelta(hours=settings.PHOTO_PENDING_GIVE_UP_HOURS)
    given_up = 0
    for photo_id in pending.filter(created_at__lt=give_up_before).values_list("pk", flat=True):
        given_up += _give_up_photo(photo_id)

    retry_before = now - timedelta(minutes=settings.PHOTO_PENDING_RETRY_AFTER_MINUTES)
    retry_ids = list(
        pending.filter(created_at__lt=retry_before, created_at__gte=give_up_before).values_list(
            "pk", flat=True
        )
    )
    for photo_id in retry_ids:
        process_sighting_photo.delay(photo_id)

    return QuarantineSweep(
        retried=len(retry_ids),
        given_up=given_up,
        orphans_deleted=_delete_quarantine_orphans(now),
    )


def _give_up_photo(photo_id: int) -> int:
    with transaction.atomic():
        photo = (
            SightingPhoto.objects.select_for_update()
            .filter(pk=photo_id, status=PhotoStatus.PENDING)
            .first()
        )
        if photo is None:
            return 0
        storage, name = photo.original.storage, photo.original.name
        photo.status = PhotoStatus.REJECTED
        photo.original = ""
        photo.save(update_fields=["status", "original", "updated_at"])
        if name:
            transaction.on_commit(lambda: storage.delete(name))
    return 1


def _delete_quarantine_orphans(now: datetime) -> int:
    storage = quarantine_storage()
    # Исходников в карантине мало по построению: они живут до обработки.
    referenced = set(SightingPhoto.objects.exclude(original="").values_list("original", flat=True))
    # Запас по времени: файл пишется до коммита записи о фото, и в этом окне
    # он выглядит сиротой, хотя приём ещё идёт.
    cutoff = now - timedelta(hours=settings.QUARANTINE_ORPHAN_GRACE_HOURS)

    deleted = 0
    for name in walk_files(storage):
        if name in referenced or storage.get_modified_time(name) >= cutoff:
            continue
        storage.delete(name)
        deleted += 1
    return deleted
