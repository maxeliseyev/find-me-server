"""Корень публичного API. Роуты приложений подключаются сюда по мере готовности."""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.reports.urls")),
    path("", include("apps.sightings.urls")),
    path("", include("apps.geo.urls")),
]
