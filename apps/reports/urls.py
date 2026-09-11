from django.urls import path

from .views import LostReportCreateView, MapViewportView

urlpatterns = [
    path("reports/", LostReportCreateView.as_view(), name="report-create"),
    path("map/", MapViewportView.as_view(), name="map-viewport"),
]
