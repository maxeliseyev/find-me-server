"""Публичные API объявлений."""

from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .map import map_features, viewport_polygon


class MapViewportSerializer(serializers.Serializer):
    min_lon = serializers.FloatField(min_value=-180, max_value=180)
    min_lat = serializers.FloatField(min_value=-90, max_value=90)
    max_lon = serializers.FloatField(min_value=-180, max_value=180)
    max_lat = serializers.FloatField(min_value=-90, max_value=90)
    zoom = serializers.IntegerField(min_value=0, max_value=22, default=13)

    def validate(self, attrs):
        if attrs["min_lon"] >= attrs["max_lon"] or attrs["min_lat"] >= attrs["max_lat"]:
            raise serializers.ValidationError(
                "Границы bbox должны идти от меньшей координаты к большей."
            )
        return attrs


class MapViewportView(APIView):
    """GET /api/v1/map/ — GeoJSON точек карты для заданного bbox."""

    permission_classes = [AllowAny]

    def get(self, request):
        serializer = MapViewportSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        bbox = viewport_polygon(
            min_lon=data["min_lon"],
            min_lat=data["min_lat"],
            max_lon=data["max_lon"],
            max_lat=data["max_lat"],
        )

        return Response(
            {
                "type": "FeatureCollection",
                "features": map_features(bbox=bbox, zoom=data["zoom"]),
            }
        )
