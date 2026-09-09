from celery import shared_task


@shared_task
def fanout_new_report(report_id: int) -> int:
    """Разослать новое объявление подписчикам района (раздел 8)."""
    raise NotImplementedError


@shared_task
def fanout_new_sighting(sighting_id: int) -> int:
    """Разослать новую отметку.

    Отметки «животное у меня» проходят сквозь тихие часы, остальные — нет.
    """
    raise NotImplementedError


@shared_task
def send_telegram_message(user_id: int, text: str, event_key: str) -> None:
    """Отправка одного сообщения с учётом дедупа и суточного потолка."""
    raise NotImplementedError
