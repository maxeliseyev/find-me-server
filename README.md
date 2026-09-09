# Find Me — сервис поиска потерянных животных

Бэкенд сервиса, где первичная сущность — **отметка о наблюдении**, а не объявление.
Спецификация: [docs/spec-poisk-zhivotnyh.md](docs/spec-poisk-zhivotnyh.md).

## Стек

- Python 3.13, Django 5.2 LTS + GeoDjango
- PostgreSQL 16 + PostGIS, все координаты — `geography(Point, 4326)`
- Redis: кэш, брокер, дедупликация уведомлений
- Celery + beat: фан-аут уведомлений, пересчёт зон поиска, обработка фото
- aiogram: Telegram-бот отдельным процессом, БД общая
- uv: зависимости и запуск

## Быстрый старт

```bash
brew install gdal geos proj        # системные библиотеки для GeoDjango
cp .env.example .env
make install                       # uv sync --all-extras
make up                            # postgis + redis в docker (compose)
make migrate
make superuser
make run                           # http://localhost:8000/admin/
```

Фоновые задачи — `make worker` и `make beat`, бот — `make bot`.
Всё целиком в докере: `docker compose up` (бот — `docker compose --profile bot up`).

На Apple Silicon в compose используется multi-arch образ `imresamu/postgis`:
официальный `postgis/postgis` собран только под amd64.
Если в системе нет compose-плагина, работает `docker-compose` из homebrew.

## Структура

```
config/            настройки (base/local/production/test), celery, urls
apps/
  core/            базовые модели, enum'ы, гео- и фото-утилиты, healthz
  accounts/        пользователь: telegram_id, trust_score, бан
  pets/            животное (отделено от объявления: теряться можно дважды)
  reports/         объявления о пропаже, публично — смещённая точка
  sightings/       отметки, веса, зона поиска — ядро продукта
  geo/             гео-подписки, фан-аут, журнал уведомлений
  moderation/      жалобы, автоскрытие, лог действий модератора
  chat/            диалоги владелец ↔ очевидец
bot/               aiogram: авторизация, «следить за районом»
docker/            Dockerfile
```

## Что заложено из спеки, но ещё не реализовано

Скелет содержит модели, админку и точки входа. Помечено `NotImplementedError` / `TODO`:

- `apps/sightings/weights.py` — вес отметки (раздел 6.2)
- `apps/sightings/zones.py` — ядерная оценка плотности, вектор движения (6.3)
- `apps/geo/tasks.py` — фан-аут, тихие часы, суточный потолок (8)
- `apps/core/images.py` — чтение GPS из EXIF и его вырезание (9)
- `apps/accounts/services.py` — авторизация через Telegram, репутация
- API-роуты приложений (`urls.py` пустые) — этап 1

## Решения, зафиксированные в коде

- **Отметку можно поставить без регистрации**: `Sighting.author` и `Sighting.report`
  оба nullable. Это принципиально, см. раздел 5 спеки.
- **Точка пропажи не публикуется точной**: `LostReport.public_geog` отдаёт смещение
  на `PUBLIC_LOCATION_BLUR_M`, детерминированное по id объявления, чтобы точку
  нельзя было усреднить по нескольким запросам.
- **EXIF режется перед отдачей**, GPS из него используется до этого (`SightingPhoto.exif_stripped`).
- **Уведомления логируются** (`NotificationLog`) — без этого не сделать дедуп и потолок.

## Открыто (раздел 12 спеки)

Монетизация, город пилота, поставщик тайлов, верификация по телефону, автоархив.
Решение по монетизации нужно до этапа 1: платное продвижение — отдельная подсистема.
