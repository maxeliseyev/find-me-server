from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import TimeStampedModel


class AbuseReason(models.TextChoices):
    SPAM = "spam", "Спам или реклама"
    FAKE = "fake", "Фейковая отметка"
    EXTORTION = "extortion", "Вымогательство"
    ABUSE = "abuse", "Оскорбления"
    OTHER = "other", "Другое"


class AbuseReport(TimeStampedModel):
    """Жалоба на отметку или объявление (раздел 9).

    При N жалобах цель автоматически скрывается до разбора.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="abuse_reports",
    )
    reason = models.CharField("причина", max_length=16, choices=AbuseReason)
    comment = models.TextField("комментарий", blank=True)

    resolved_at = models.DateTimeField("разобрано", null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_abuse_reports",
    )

    class Meta:
        verbose_name = "жалоба"
        verbose_name_plural = "жалобы"
        ordering = ("resolved_at", "-created_at")
        indexes = [models.Index(fields=["content_type", "object_id"], name="abuse_target_idx")]


class ModerationAction(TimeStampedModel):
    """Лог действий модератора — обязателен по разделу 9."""

    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="mod_actions"
    )
    action = models.CharField("действие", max_length=64)
    target_repr = models.CharField("объект", max_length=255)
    note = models.TextField("комментарий", blank=True)

    class Meta:
        verbose_name = "действие модератора"
        verbose_name_plural = "лог модерации"
        ordering = ("-created_at",)
