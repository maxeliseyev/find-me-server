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
def process_sighting_photo(photo_id: int) -> None:
    """Прочитать GPS из EXIF, вырезать метаданные, сделать превью."""
    raise NotImplementedError
