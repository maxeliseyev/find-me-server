"""Выборка подписчиков под событие (раздел 8).

Запрос из спеки:

    SELECT user_id FROM geo_subscriptions
    WHERE active
      AND ST_DWithin(geog, :point, radius_m)
      AND (species_filter IS NULL OR :species = ANY(species_filter));
"""

from django.contrib.gis.db.models.functions import Distance
from django.db.models import F, Q

from .models import GeoSubscription


def subscribers_for(point, species: str | None = None):
    qs = (
        GeoSubscription.objects.filter(active=True, user__is_banned=False)
        .annotate(distance=Distance("geog", point))
        .filter(distance__lte=F("radius_m"))
    )
    if species:
        qs = qs.filter(Q(species_filter__len=0) | Q(species_filter__contains=[species]))
    return qs.select_related("user")
