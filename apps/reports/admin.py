from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import LostReport


@admin.register(LostReport)
class LostReportAdmin(gis_admin.GISModelAdmin):
    list_display = ("__str__", "author", "status", "last_seen_at", "created_at")
    list_filter = ("status", "pet__species", "location_precision")
    search_fields = ("pet__name", "pet__breed", "pet__features", "author__username")
    autocomplete_fields = ("pet", "author")
    date_hierarchy = "last_seen_at"
