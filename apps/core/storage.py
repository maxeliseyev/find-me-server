"""Хранилища пользовательских файлов."""

from django.core.files.storage import storages


def quarantine_storage():
    """Приватное хранилище исходников до серверной обработки.

    Callable, а не экземпляр: иначе миграция зафиксирует конкретный бэкенд
    и настройки окружения, в котором её создали.
    """
    return storages["quarantine"]
