"""Безопасная обработка пользовательских изображений."""

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
GPS_INFO_TAG = 34853


class ImageProcessingError(ValueError):
    """Файл нельзя безопасно обработать как изображение."""


@dataclass(frozen=True)
class SanitizedImage:
    """Перекодированное изображение, готовое к публикации."""

    content: ContentFile
    sha256: str


def extract_gps(image_file) -> tuple[float, float] | None:
    """Вернуть (lon, lat) из GPS EXIF или None, не меняя файл."""
    with _open_image(image_file) as image:
        gps = image.getexif().get_ifd(GPS_INFO_TAG)

    if not gps:
        return None

    try:
        lat = _gps_coordinate(gps[2], gps[1])
        lon = _gps_coordinate(gps[4], gps[3])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return None
    return lon, lat


def sanitize_image(image_file) -> SanitizedImage:
    """Перекодировать изображение в WebP без EXIF и с ограничением размера."""
    with _open_image(image_file) as image:
        normalized = ImageOps.exif_transpose(image)
        normalized.thumbnail(
            (settings.IMAGE_MAX_DIMENSION, settings.IMAGE_MAX_DIMENSION), Image.Resampling.LANCZOS
        )
        if normalized.mode not in {"RGB", "RGBA"}:
            normalized = normalized.convert("RGBA" if "A" in normalized.getbands() else "RGB")

        output = BytesIO()
        normalized.save(output, format="WEBP", quality=settings.IMAGE_WEBP_QUALITY, method=6)

    payload = output.getvalue()
    return SanitizedImage(
        content=ContentFile(payload, name=f"{uuid4().hex}.webp"),
        sha256=sha256(payload).hexdigest(),
    )


def strip_exif(image_file) -> ContentFile:
    """Совместимый короткий путь: вернуть очищенное содержимое изображения."""
    return sanitize_image(image_file).content


def _open_image(image_file):
    try:
        image_file.seek(0)
        if (
            getattr(image_file, "size", None) is not None
            and image_file.size > settings.IMAGE_MAX_UPLOAD_BYTES
        ):
            raise ImageProcessingError("Размер изображения превышает допустимый.")
        image = Image.open(image_file)
        if image.width * image.height > settings.IMAGE_MAX_PIXELS:
            raise ImageProcessingError("Разрешение изображения превышает допустимое.")
        image.load()
    except ImageProcessingError:
        raise
    except (OSError, UnidentifiedImageError) as error:
        raise ImageProcessingError("Файл не является допустимым изображением.") from error
    finally:
        image_file.seek(0)

    if image.format not in SUPPORTED_FORMATS:
        image.close()
        raise ImageProcessingError("Поддерживаются только JPEG, PNG и WebP.")
    return image


def _gps_coordinate(value, reference: str) -> float:
    degrees, minutes, seconds = (float(part) for part in value)
    coordinate = degrees + minutes / 60 + seconds / 3600
    return -coordinate if reference in {"S", "W"} else coordinate
