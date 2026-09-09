from celery import shared_task


@shared_task
def archive_stale_reports() -> int:
    """Автоархив объявлений, которые никто не закрыл (открытый вопрос 12.2).

    TODO: срок и правило согласовать до этапа 1.
    """
    raise NotImplementedError
