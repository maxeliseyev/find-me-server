"""Безопасная обработка пользовательских изображений."""

from hashlib import sha256
from io import BytesIO
from re import fullmatch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.images import ImageProcessingError, extract_gps, sanitize_image


def image_file(*, size=(20, 10), gps=None, description=None) -> SimpleUploadedFile:
    image = Image.new("RGB", size, "orange")
    exif = Image.Exif()
    if description:
        exif[270] = description
    if gps:
        exif[34853] = gps

    output = BytesIO()
    image.save(output, "JPEG", exif=exif)
    return SimpleUploadedFile("owner-home.jpg", output.getvalue(), content_type="image/jpeg")


def test_extract_gps_reads_coordinates_before_metadata_is_removed():
    photo = image_file(gps={1: "N", 2: (55, 45, 30), 3: "E", 4: (37, 36, 15)})

    assert extract_gps(photo) == pytest.approx((37.6041667, 55.7583333))


def test_sanitize_image_removes_exif_and_uses_random_webp_name():
    photo = image_file(description="Снято у дома владельца")

    sanitized = sanitize_image(photo)

    assert fullmatch(r"[0-9a-f]{32}\.webp", sanitized.content.name)
    assert sanitized.sha256 == sha256(sanitized.content.read()).hexdigest()
    sanitized.content.seek(0)
    with Image.open(sanitized.content) as result:
        assert result.format == "WEBP"
        assert result.getexif() == {}


def test_sanitize_image_resizes_large_photo(settings):
    settings.IMAGE_MAX_DIMENSION = 100
    photo = image_file(size=(400, 200))

    sanitized = sanitize_image(photo)

    with Image.open(sanitized.content) as result:
        assert result.size == (100, 50)


def test_sanitize_image_rejects_non_image_file():
    file = SimpleUploadedFile("photo.jpg", b"not an image", content_type="image/jpeg")

    with pytest.raises(ImageProcessingError, match="допустимым изображением"):
        sanitize_image(file)


def test_sanitize_image_rejects_excessive_pixel_count(settings):
    settings.IMAGE_MAX_PIXELS = 100
    photo = image_file(size=(20, 10))

    with pytest.raises(ImageProcessingError, match="Разрешение"):
        sanitize_image(photo)
