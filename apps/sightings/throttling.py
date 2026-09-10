"""Рейтлимиты постановки отметок.

Отметку ставят без регистрации (инвариант 1), поэтому для анонимного вызова
это единственная защита от спама и увода поиска — снимать её «для удобства»
нельзя (инвариант 12). Ставки — в `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonSightingThrottle(AnonRateThrottle):
    scope = "anon_sighting"


class UserSightingThrottle(UserRateThrottle):
    scope = "user_sighting"
