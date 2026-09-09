from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Проверка живости: приложение поднялось и видит БД."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:  # эндпоинт не должен падать сам
        db_ok = False

    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok})
