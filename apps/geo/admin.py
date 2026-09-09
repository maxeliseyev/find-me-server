from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import GeoSubscription, NotificationLog


@admin.register(GeoSubscription)
class GeoSubscriptionAdmin(gis_admin.GISModelAdmin):
    list_display = ("__str__", "user", "radius_m", "active", "created_at")
    list_filter = ("active",)
    autocomplete_fields = ("user",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "event_key", "delivered", "suppressed_reason", "created_at")
    list_filter = ("delivered", "suppressed_reason")
    search_fields = ("event_key", "user__username")
