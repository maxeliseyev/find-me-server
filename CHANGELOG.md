# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/). Версия — semver
`major.minor.patch`. Источник правды: файл `VERSION`. Как бампать: `docs/versioning.md`.

## 0.2.0 — 2026-09-10

### Added

- `POST /api/v1/sightings/` — постановка отметки без регистрации: анонимно,
  с привязкой к активному объявлению или без неё. Рейтлимиты
  `anon_sighting` / `user_sighting`, отказ забаненным, валидация координат
  и времени наблюдения.
- `GET /api/v1/sightings/<id>/` — одна отметка; скрытые и спам наружу
  не отдаются, автор в ответе не раскрывается.
- Тесты: `tests/test_sightings_api.py` (10) и инварианты 1 и 12 на уровне API.

## 0.1.1 — 2026-09-09

### Added

- Инварианты `AGENTS.md` стали исполняемым контрактом: `tests/test_invariants.py`
  с номером инварианта в имени теста (анонимная отметка, переживание объявления,
  смещение публичной точки, geography+GiST, независимость `seen_at`).
- `pre-push` хук: `make check` до отправки ветки; тесты пропускаются с
  предупреждением, если PostGIS не поднят.
- `make session-start` — ритуал старта смены одной командой.
- Dependabot: экшены и `uv.lock` раз в месяц, отдельными группами.

### Changed

- Джобы `lint`, `test`, `contract` обязательны для мержа в `main`
  (required status checks в ruleset).
- `docs/git-workflow.md`: раздел про stacked-ветки — «Update branch» после
  squash-мержа базового PR откатывает файлы, правильный путь `rebase --onto`.

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
