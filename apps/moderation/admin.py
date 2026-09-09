from django.contrib import admin

from .models import AbuseReport, ModerationAction


@admin.register(AbuseReport)
class AbuseReportAdmin(admin.ModelAdmin):
    """Очередь жалоб — рабочий инструмент модератора (раздел 9)."""

    list_display = ("id", "reason", "target", "reporter", "created_at", "resolved_at")
    list_filter = ("reason", ("resolved_at", admin.EmptyFieldListFilter), "content_type")
    search_fields = ("comment",)
    date_hierarchy = "created_at"


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "moderator", "action", "target_repr")
    list_filter = ("action",)
    readonly_fields = ("created_at", "moderator", "action", "target_repr", "note")
