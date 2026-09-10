"""Сериализаторы отметок.

Главный сценарий продукта — «открыл ссылку, поставил точку, закрыл»
(раздел 3.1 спеки), поэтому вход максимально короткий: точка, время, вид.
Всё остальное необязательно.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.core.enums import Species
from apps.reports.models import LostReport, ReportStatus

from .models import Confidence, Sighting, SightingSource, SightingStatus

# Часы вперёд, которые прощаем криво выставленным часам устройства.
FUTURE_TOLERANCE_MINUTES = 5


class SightingSerializer(serializers.ModelSerializer):
    """Публичное представление отметки.

    Автор не раскрывается: отметки анонимных пользователей не должны выдавать
    о них ничего лишнего (раздел 9 спеки).
    """

    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()

    class Meta:
        model = Sighting
        fields = (
            "id",
            "lat",
            "lon",
            "seen_at",
            "created_at",
            "source",
            "species",
            "colors",
            "comment",
            "confidence",
            "animal_in_custody",
            "report",
        )
        read_only_fields = fields

    def get_lat(self, obj: Sighting) -> float:
        return obj.geog.y

    def get_lon(self, obj: Sighting) -> float:
        return obj.geog.x


class SightingCreateSerializer(serializers.Serializer):
    """Постановка отметки. Работает и без авторизации, и без объявления."""

    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    seen_at = serializers.DateTimeField()
    source = serializers.ChoiceField(choices=SightingSource.choices)

    report = serializers.PrimaryKeyRelatedField(
        queryset=LostReport.objects.filter(status=ReportStatus.ACTIVE),
        required=False,
        allow_null=True,
    )
    species = serializers.ChoiceField(choices=Species.choices, required=False, allow_blank=True)
    colors = serializers.ListField(
        child=serializers.CharField(max_length=32), required=False, default=list
    )
    comment = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    confidence = serializers.ChoiceField(choices=Confidence.choices, default=Confidence.MAYBE)
    animal_in_custody = serializers.BooleanField(default=False)

    def validate_seen_at(self, value):
        if value > timezone.now() + timezone.timedelta(minutes=FUTURE_TOLERANCE_MINUTES):
            raise serializers.ValidationError("Время наблюдения не может быть в будущем.")
        return value

    def create(self, validated_data: dict) -> Sighting:
        from django.contrib.gis.geos import Point

        lat = validated_data.pop("lat")
        lon = validated_data.pop("lon")

        author = self.context["request"].user
        author = author if author.is_authenticated else None

        return Sighting.objects.create(
            geog=Point(lon, lat, srid=4326),
            author=author,
            status=SightingStatus.VISIBLE,
            **validated_data,
        )
