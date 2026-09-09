from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.enums import Species
from apps.core.models import TimeStampedModel


class SightingSource(models.TextChoices):
    DEVICE_GPS = "device_gps", "Геолокация устройства"
    MANUAL_PIN = "manual_pin", "Точка на карте"


class Confidence(models.TextChoices):
    SURE = "sure", "Уверен"
    MAYBE = "maybe", "Возможно"
    UNSURE = "unsure", "Не уверен"


class SightingStatus(models.TextChoices):
    VISIBLE = "visible", "Видна"
    HIDDEN = "hidden", "Скрыта"
    SPAM = "spam", "Спам"


class Sighting(TimeStampedModel):
    """Отметка о наблюдении — центральная сущность сервиса.

    `report` и `author` nullable намеренно (раздел 5): половина полезных сообщений —
    «видел рыжего кота у пятого дома, не знаю чей», и отметка должна сохраняться
    до любой регистрации.
    """

    report = models.ForeignKey(
        "reports.LostReport",
        verbose_name="объявление",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sightings",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="автор",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sightings",
    )

    geog = gis_models.PointField("точка", geography=True, srid=4326, spatial_index=True)
    seen_at = models.DateTimeField("когда видели")
    source = models.CharField("источник точки", max_length=16, choices=SightingSource)

    animal_in_custody = models.BooleanField("животное у меня", default=False, db_index=True)
    species = models.CharField("вид", max_length=16, choices=Species, blank=True)
    colors = ArrayField(models.CharField(max_length=32), verbose_name="окрас", default=list)
    comment = models.TextField("комментарий", blank=True)
    confidence = models.CharField(
        "уверенность", max_length=16, choices=Confidence, default=Confidence.MAYBE
    )

    # Раздел 6.2: weight = w_recency × w_source × w_trust × w_confidence.
    # Хранится посчитанным, пересчитывается фоновой задачей.
    weight = models.FloatField("вес", default=0.0)

    status = models.CharField(
        "статус",
        max_length=16,
        choices=SightingStatus,
        default=SightingStatus.VISIBLE,
        db_index=True,
    )

    class Meta:
        verbose_name = "отметка о наблюдении"
        verbose_name_plural = "отметки о наблюдениях"
        ordering = ("-seen_at",)
        indexes = [
            models.Index(fields=["report", "-seen_at"], name="sighting_report_seen_idx"),
        ]

    def __str__(self):
        return f"Отметка {self.pk} от {self.seen_at:%d.%m %H:%M}"


class SightingPhoto(TimeStampedModel):
    """Фото к отметке.

    EXIF читаем на сервере (может дать координаты) и вырезаем перед отдачей — раздел 9.
    """

    sighting = models.ForeignKey(Sighting, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField("фото", upload_to="sightings/%Y/%m/")
    exif_stripped = models.BooleanField("EXIF вырезан", default=False)

    class Meta:
        verbose_name = "фото отметки"
        verbose_name_plural = "фото отметок"


class SearchZone(TimeStampedModel):
    """Расчётная зона поиска по объявлению (раздел 6.3).

    Считается фоновой задачей по взвешенным точкам, кэшируется в Redis,
    клиенту отдаётся как GeoJSON. Здесь — последний посчитанный снимок.
    """

    report = models.OneToOneField(
        "reports.LostReport", on_delete=models.CASCADE, related_name="search_zone"
    )
    polygon = gis_models.MultiPolygonField("зона", geography=True, srid=4326, null=True)
    heatmap = models.JSONField("тепловая карта, GeoJSON", default=dict)
    direction_deg = models.FloatField("вектор движения, градусы", null=True, blank=True)
    computed_at = models.DateTimeField("посчитано", auto_now=True)

    class Meta:
        verbose_name = "зона поиска"
        verbose_name_plural = "зоны поиска"
