# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/). Версия — semver
`major.minor.patch`. Источник правды: файл `VERSION`. Как бампать: `docs/versioning.md`.

## 0.1.0 — 2026-09-09

### Added

- Скелет проекта: Django 5.2 LTS + GeoDjango, Python 3.13, зависимости через `uv`.
- Настройки разбиты на `base` / `local` / `production` / `test`; Celery с
  beat-расписанием (пересчёт зон, автоархив объявлений).
- Приложения по модели данных спеки: `core`, `accounts`, `pets`, `reports`,
  `sightings`, `geo`, `moderation`, `chat`; миграции проверены на PostGIS 3.5.
- Telegram-бот на aiogram отдельным процессом на общей БД.
- `docker-compose` (postgis, redis, web, worker, beat, bot), `Dockerfile`, `Makefile`.
- Контракт репозитория: `AGENTS.md`, `docs/status.md`, `docs/handoff.md`,
  `docs/git-workflow.md`, `docs/versioning.md`, ADR в `docs/decisions/`.
- CI (ruff, pytest на живом PostGIS, `makemigrations --check`, сверка
  `status.md` с веткой), шаблон PR, pre-commit хук против коммитов в `main`.
