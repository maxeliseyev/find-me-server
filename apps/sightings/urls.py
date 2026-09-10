from django.urls import path

from .views import SightingCreateView, SightingDetailView

urlpatterns = [
    path("sightings/", SightingCreateView.as_view(), name="sighting-create"),
    path("sightings/<int:pk>/", SightingDetailView.as_view(), name="sighting-detail"),
]
