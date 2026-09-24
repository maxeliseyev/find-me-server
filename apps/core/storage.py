"""Хранилища пользовательских файлов."""

from django.core.files.storage import storages


def quarantine_storage():
    """Приватное хранилище исходников до серверной обработки.

    Callable, а не экземпляр: иначе миграция зафиксирует конкретный бэкенд
    и настройки окружения, в котором её создали.
    """
    return storages["quarantine"]


def walk_files(storage, path: str = ""):
    """Все имена файлов в хранилище под `path`, рекурсивно."""
    directories, files = storage.listdir(path)
    for name in files:
        yield f"{path}/{name}" if path else name
    for directory in directories:
        yield from walk_files(storage, f"{path}/{directory}" if path else directory)
