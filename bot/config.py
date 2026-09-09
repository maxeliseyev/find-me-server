import os

import django


def setup_django() -> None:
    """Бот — отдельный процесс, но БД общая (раздел 7)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    django.setup()
