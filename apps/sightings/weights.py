"""Вес отметки (раздел 6.2).

    weight = w_recency × w_source × w_trust × w_confidence

Кошки прячутся рядом, собаки уходят далеко — период полураспада зависит от вида
(settings.SIGHTING_HALF_LIFE_HOURS).
"""

W_SOURCE = {"device_gps": 1.0, "manual_pin": 0.6}
W_CONFIDENCE = {"sure": 1.0, "maybe": 0.7, "unsure": 0.4}


def recency_weight(seen_at, species: str, *, now=None) -> float:
    """Экспоненциальное затухание по времени. TODO(этап 2)."""
    raise NotImplementedError


def trust_weight(author) -> float:
    """Множитель по репутации автора; для анонимных отметок — базовое значение."""
    raise NotImplementedError


def compute_weight(sighting, *, now=None) -> float:
    raise NotImplementedError
