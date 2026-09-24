from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import SearchZone, Sighting, SightingPhoto


class SightingPhotoInline(admin.TabularInline):
    """Только просмотр: загрузка из админки обошла бы очистку EXIF.

    Исходник из карантина и точку из EXIF модератору не показываем.
    """

    model = SightingPhoto
    extra = 0
    fields = ("image", "status", "exif_stripped", "sha256", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sighting)
class SightingAdmin(gis_admin.GISModelAdmin):
    list_display = (
        "__str__",
        "report",
        "author",
        "species",
        "source",
        "confidence",
        "animal_in_custody",
        "weight",
        "status",
    )
    list_filter = ("status", "species", "source", "confidence", "animal_in_custody")
    search_fields = ("comment", "author__username")
    autocomplete_fields = ("report", "author")
    date_hierarchy = "seen_at"
    inlines = [SightingPhotoInline]
    actions = ["hide_sightings", "mark_spam"]

    @admin.action(description="Скрыть отметки")
    def hide_sightings(self, request, queryset):
        queryset.update(status="hidden")

    @admin.action(description="Пометить как спам")
    def mark_spam(self, request, queryset):
        queryset.update(status="spam")


@admin.register(SearchZone)
class SearchZoneAdmin(gis_admin.GISModelAdmin):
    list_display = ("report", "direction_deg", "computed_at")
