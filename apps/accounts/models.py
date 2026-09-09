from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь. Основная авторизация — Telegram (раздел 8).

    Пароль и email остаются от AbstractUser: ими пользуются модераторы в админке.
    """

    telegram_id = models.BigIntegerField("Telegram ID", unique=True, null=True, blank=True)
    telegram_username = models.CharField("Telegram username", max_length=64, blank=True)
    display_name = models.CharField("отображаемое имя", max_length=128, blank=True)

    phone_verified = models.BooleanField("телефон подтверждён", default=False)

    # Раздел 6.2 / 9: репутация влияет на вес отметок автора.
    trust_score = models.IntegerField("репутация", default=0, db_index=True)
    is_banned = models.BooleanField("забанен", default=False, db_index=True)
    banned_reason = models.TextField("причина бана", blank=True)

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return self.display_name or self.telegram_username or self.username or f"user#{self.pk}"
