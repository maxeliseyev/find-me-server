from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.core.geo import blur_point
from apps.core.models import TimeStampedModel


class LocationPrecision(models.TextChoices):
    EXACT = "exact", "Точная"
    BLURRED = "blurred", "Смещённая"


class ReportStatus(models.TextChoices):
    ACTIVE = "active", "Активно"
    FOUND = "found", "Найдено"
    ARCHIVED = "archived", "Архив"
    HIDDEN = "hidden", "Скрыто модератором"


class LostReport(TimeStampedModel):
    """Объявление о пропаже."""

    pet = models.ForeignKey(
        "pets.Pet", verbose_name="животное", on_delete=models.CASCADE, related_name="reports"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="автор",
        on_delete=models.CASCADE,
        related_name="lost_reports",
    )

    last_seen_at = models.DateTimeField("последний раз видели")
    last_seen_geog = gis_models.PointField(
        "точка пропажи", geography=True, srid=4326, spatial_index=True
    )
    # Раздел 9: точка пропажи — обычно подъезд владельца.
    location_precision = models.CharField(
        "публичная точность",
        max_length=16,
        choices=LocationPrecision,
        default=LocationPrecision.BLURRED,
    )
    search_radius_m = models.PositiveIntegerField("радиус поиска, м", default=2000)

    status = models.CharField(
        "статус", max_length=16, choices=ReportStatus, default=ReportStatus.ACTIVE, db_index=True
    )
    reward_text = models.TextField("вознаграждение", blank=True)

    class Meta:
        verbose_name = "объявление о пропаже"
        verbose_name_plural = "объявления о пропаже"
        ordering = ("-created_at",)
        indexes = [
            gis_models.Index(
                fields=["last_seen_geog"],
                name="lostreport_geog_active_gix",
                condition=models.Q(status="active"),
            ),
        ]

    def __str__(self):
        return f"{self.pet} — {self.get_status_display()}"

    @property
    def public_geog(self):
        """Точка для публичной выдачи: точная только по решению владельца."""
        if self.location_precision == LocationPrecision.EXACT:
            return self.last_seen_geog
        return blur_point(self.last_seen_geog, seed=f"report:{self.pk}")
