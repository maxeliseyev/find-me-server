from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("__str__", "telegram_id", "trust_score", "is_banned", "date_joined")
    list_filter = ("is_banned", "phone_verified", "is_staff")
    search_fields = ("username", "telegram_username", "telegram_id", "display_name")
    fieldsets = (
        *BaseUserAdmin.fieldsets,
        (
            "Профиль сервиса",
            {
                "fields": (
                    "telegram_id",
                    "telegram_username",
                    "display_name",
                    "phone_verified",
                    "trust_score",
                    "is_banned",
                    "banned_reason",
                )
            },
        ),
    )
