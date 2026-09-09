import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("find_me")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Раздел 6.3: зоны поиска пересчитываются по расписанию, не только по событию.
    "recalc-search-zones": {
        "task": "apps.sightings.tasks.recalc_active_search_zones",
        "schedule": crontab(minute="*/15"),
    },
    # Раздел 12.2: автоархив объявлений, которые никто не закрыл.
    "archive-stale-reports": {
        "task": "apps.reports.tasks.archive_stale_reports",
        "schedule": crontab(hour=4, minute=0),
    },
}
