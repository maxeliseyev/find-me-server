from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.core.enums import Species
from apps.core.models import TimeStampedModel


class GeoSubscription(TimeStampedModel):
    """Гео-подписка волонтёра или владельца (раздел 3.3).

    Владельцу подписка на радиус вокруг точки пропажи создаётся автоматически.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        on_delete=models.CASCADE,
        related_name="geo_subscriptions",
    )
    title = models.CharField("название", max_length=64, blank=True)
    geog = gis_models.PointField("центр", geography=True, srid=4326, spatial_index=True)
    radius_m = models.PositiveIntegerField("радиус, м", default=1500)
    species_filter = ArrayField(
        models.CharField(max_length=16, choices=Species),
        verbose_name="фильтр по видам",
        default=list,
        blank=True,
    )
    active = models.BooleanField("активна", default=True, db_index=True)
    # Раздел 8: тихие часы, по умолчанию 22:00–09:00.
    quiet_from_hour = models.PositiveSmallIntegerField("тихие часы с", default=22)
    quiet_to_hour = models.PositiveSmallIntegerField("тихие часы до", default=9)

    class Meta:
        verbose_name = "гео-подписка"
        verbose_name_plural = "гео-подписки"
        indexes = [
            gis_models.Index(
                fields=["geog"],
                name="geosub_geog_active_gix",
                condition=models.Q(active=True),
            ),
        ]

    def __str__(self):
        return f"{self.title or 'Район'} {self.radius_m} м — {self.user}"


class NotificationLog(TimeStampedModel):
    """Журнал отправок.

    Нужен для дедупликации и потолка уведомлений в сутки (раздел 8) —
    самое хрупкое место продукта: люди отписываются от спама и не возвращаются.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    subscription = models.ForeignKey(
        GeoSubscription, on_delete=models.SET_NULL, null=True, blank=True
    )
    event_key = models.CharField("ключ события", max_length=128, db_index=True)
    delivered = models.BooleanField("доставлено", default=False)
    suppressed_reason = models.CharField("почему не отправлено", max_length=64, blank=True)

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "уведомления"
        indexes = [models.Index(fields=["user", "-created_at"], name="notiflog_user_created_idx")]
