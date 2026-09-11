"""Сериализаторы объявлений.

Важно: в публичную выдачу попадает `public_geog`, а не `last_seen_geog`.
"""

from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.core.enums import Sex, Size, Species
from apps.pets.models import Pet

from .models import LocationPrecision, LostReport, ReportStatus

# Часы вперёд, которые прощаем криво выставленным часам устройства.
FUTURE_TOLERANCE_MINUTES = 5


class PetCreateSerializer(serializers.Serializer):
    """Данные животного, создаваемого вместе с объявлением."""

    name = serializers.CharField(max_length=64, required=False, allow_blank=True)
    species = serializers.ChoiceField(choices=Species.choices)
    breed = serializers.CharField(max_length=128, required=False, allow_blank=True)
    colors = serializers.ListField(
        child=serializers.CharField(max_length=32), required=False, default=list
    )
    size = serializers.ChoiceField(choices=Size.choices, required=False, allow_blank=True)
    sex = serializers.ChoiceField(choices=Sex.choices, required=False, default=Sex.UNKNOWN)
    features = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    chip_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    brand_number = serializers.CharField(max_length=32, required=False, allow_blank=True)


class LostReportCreateSerializer(serializers.Serializer):
    """Создать активное объявление и принадлежащее владельцу животное."""

    pet = PetCreateSerializer()
    last_seen_at = serializers.DateTimeField()
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    location_precision = serializers.ChoiceField(
        choices=LocationPrecision.choices, default=LocationPrecision.BLURRED
    )
    search_radius_m = serializers.IntegerField(min_value=1, required=False, default=2000)
    reward_text = serializers.CharField(max_length=2000, required=False, allow_blank=True)

    def validate_last_seen_at(self, value):
        if value > timezone.now() + timezone.timedelta(minutes=FUTURE_TOLERANCE_MINUTES):
            raise serializers.ValidationError(
                "Время последнего наблюдения не может быть в будущем."
            )
        return value

    @transaction.atomic
    def create(self, validated_data: dict) -> LostReport:
        pet_data = validated_data.pop("pet")
        lat = validated_data.pop("lat")
        lon = validated_data.pop("lon")
        author = self.context["request"].user

        pet = Pet.objects.create(owner=author, **pet_data)
        return LostReport.objects.create(
            pet=pet,
            author=author,
            last_seen_geog=Point(lon, lat, srid=4326),
            status=ReportStatus.ACTIVE,
            **validated_data,
        )


class LostReportOwnerSerializer(serializers.ModelSerializer):
    """Ответ владельцу после создания: точная точка доступна только ему."""

    lat = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    pet = PetCreateSerializer(read_only=True)

    class Meta:
        model = LostReport
        fields = (
            "id",
            "pet",
            "last_seen_at",
            "lat",
            "lon",
            "location_precision",
            "search_radius_m",
            "status",
            "reward_text",
            "created_at",
        )
        read_only_fields = fields

    def get_lat(self, obj: LostReport) -> float:
        return obj.last_seen_geog.y

    def get_lon(self, obj: LostReport) -> float:
        return obj.last_seen_geog.x
