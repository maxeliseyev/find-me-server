"""Обработка фото.

Раздел 9: GPS из EXIF — ценные данные для автопозиционирования отметки,
читаем на сервере, но обязательно вырезаем EXIF перед отдачей наружу.
"""

from django.core.files.base import ContentFile


def extract_gps(image_file) -> tuple[float, float] | None:
    """Вернуть (lon, lat) из EXIF или None. TODO(этап 1)."""
    raise NotImplementedError


def strip_exif(image_file) -> ContentFile:
    """Пересохранить изображение без метаданных. TODO(этап 1)."""
    raise NotImplementedError
