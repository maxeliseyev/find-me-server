from django.urls import path

from .views import MapViewportView

urlpatterns = [
    path("map/", MapViewportView.as_view(), name="map-viewport"),
]
