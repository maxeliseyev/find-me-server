"""Авторизация через Telegram и репутация. TODO(этап 1)."""


def authenticate_telegram(init_data: str):
    """Проверить подпись Telegram Login / WebApp initData и вернуть пользователя."""
    raise NotImplementedError


def adjust_trust(user, delta: int, reason: str) -> None:
    """Изменить репутацию: подтверждённая отметка — вверх, жалоба — вниз."""
    raise NotImplementedError
