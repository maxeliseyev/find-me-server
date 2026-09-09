from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Thread(TimeStampedModel):
    """Диалог владелец ↔ очевидец.

    Раздел 9: публичного телефона нет, весь контакт идёт здесь или в телеграме.
    """

    report = models.ForeignKey(
        "reports.LostReport", on_delete=models.CASCADE, related_name="threads"
    )
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="threads")
    sighting = models.ForeignKey(
        "sightings.Sighting", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "диалог"
        verbose_name_plural = "диалоги"


class Message(TimeStampedModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField("текст")
    is_hidden = models.BooleanField("скрыто модератором", default=False)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"
        ordering = ("created_at",)
        indexes = [models.Index(fields=["thread", "created_at"], name="message_thread_idx")]
