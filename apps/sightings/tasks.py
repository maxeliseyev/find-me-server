from dataclasses import asdict

from celery import shared_task


@shared_task
def recalc_search_zone(report_id: int) -> None:
    """Пересчёт зоны по одному объявлению — вызывается при новой отметке."""
    raise NotImplementedError


@shared_task
def recalc_active_search_zones() -> int:
    """Плановый пересчёт зон по всем активным объявлениям."""
    raise NotImplementedError


@shared_task
def process_sighting_photo(photo_id: int) -> str | None:
    """Опубликовать безопасную копию фото и удалить исходник из карантина."""
    from .services import publish_sighting_photo

    return publish_sighting_photo(photo_id)


@shared_task
def sweep_photo_quarantine() -> dict:
    """Плановая уборка карантина фото: зависшие обработки и файлы-сироты."""
    from .services import sweep_photo_quarantine as sweep

    return asdict(sweep())
