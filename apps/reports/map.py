"""Выдача точек для карты и серверная кластеризация."""

import math
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.contrib.gis.geos import Point, Polygon

from apps.sightings.models import Sighting, SightingStatus

from .models import LostReport, ReportStatus


def viewport_polygon(*, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> Polygon:
    """Построить полигон viewport в WGS 84 для PostGIS-фильтра."""
    return Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))


def map_features(*, bbox: Polygon, zoom: int) -> list[dict[str, Any]]:
    """Вернуть публичные точки активных объявлений и видимых отметок в viewport."""
    reports = (
        LostReport.objects.filter(status=ReportStatus.ACTIVE, last_seen_geog__within=bbox)
        .select_related("pet")
        .only("id", "pet__species", "last_seen_at", "last_seen_geog", "location_precision")
    )
    sightings = Sighting.objects.filter(status=SightingStatus.VISIBLE, geog__within=bbox).only(
        "id",
        "geog",
        "seen_at",
        "source",
        "species",
        "animal_in_custody",
        "report_id",
    )

    features = [report_feature(report) for report in reports]
    features.extend(sighting_feature(sighting) for sighting in sightings)
    return cluster_features(features, zoom=zoom)


def report_feature(report: LostReport) -> dict[str, Any]:
    """Сериализовать объявление, не выпуская наружу точную точку пропажи."""
    return point_feature(
        point=report.public_geog,
        properties={
            "kind": "report",
            "id": report.pk,
            "species": report.pet.species,
            "last_seen_at": report.last_seen_at.isoformat(),
        },
    )


def sighting_feature(sighting: Sighting) -> dict[str, Any]:
    """Сериализовать видимую отметку без данных автора."""
    return point_feature(
        point=sighting.geog,
        properties={
            "kind": "sighting",
            "id": sighting.pk,
            "species": sighting.species,
            "seen_at": sighting.seen_at.isoformat(),
            "source": sighting.source,
            "animal_in_custody": sighting.animal_in_custody,
            "report": sighting.report_id,
        },
    )


def point_feature(*, point: Point, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point.x, point.y]},
        "properties": properties,
    }


def cluster_features(features: list[dict[str, Any]], *, zoom: int) -> list[dict[str, Any]]:
    """Сгруппировать близкие точки в ячейки Web Mercator на стороне сервера."""
    cells: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        cells[_cluster_cell(lon=lon, lat=lat, zoom=zoom)].append(feature)

    result: list[dict[str, Any]] = []
    for cell_features in cells.values():
        if len(cell_features) == 1:
            result.append(cell_features[0])
        else:
            result.append(_cluster_feature(cell_features))
    return result


def _cluster_cell(*, lon: float, lat: float, zoom: int) -> tuple[int, int]:
    scale = 2**zoom * settings.MAP_CLUSTER_TILE_SIZE / settings.MAP_CLUSTER_CELL_PX
    mercator_y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
    return math.floor((lon + 180) / 360 * scale), math.floor(mercator_y * scale)


def _cluster_feature(features: list[dict[str, Any]]) -> dict[str, Any]:
    coordinates = [feature["geometry"]["coordinates"] for feature in features]
    counts = {
        "reports": sum(feature["properties"]["kind"] == "report" for feature in features),
        "sightings": sum(feature["properties"]["kind"] == "sighting" for feature in features),
    }
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                sum(point[0] for point in coordinates) / len(coordinates),
                sum(point[1] for point in coordinates) / len(coordinates),
            ],
        },
        "properties": {"kind": "cluster", "count": len(features), "counts": counts},
    }
