from django.urls import path

from .views import SightingCreateView, SightingDetailView, SightingPhotoUploadView

urlpatterns = [
    path("sightings/", SightingCreateView.as_view(), name="sighting-create"),
    path("sightings/<int:pk>/", SightingDetailView.as_view(), name="sighting-detail"),
    path(
        "sightings/<int:pk>/photos/",
        SightingPhotoUploadView.as_view(),
        name="sighting-photo-upload",
    ),
]
