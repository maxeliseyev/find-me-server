# Status

Updated: 2026-09-09
Stage: 1 (ядро)
Step: контракт репозитория; код этапа 1 ещё не начат
Branch: `docs/repo-contract`
PR: draft
Blockers: none

## Done

- Скелет слит в `main` коммитом `5bd003a`: Django 5.2 LTS + GeoDjango,
  приложения по модели данных спеки, миграции проверены на PostGIS 3.5,
  Celery, aiogram, docker-compose, ruff, pytest.
- На ветке `docs/repo-contract`: `AGENTS.md`, `docs/handoff.md`,
  `docs/git-workflow.md`, `docs/versioning.md`, пять ADR, `CHANGELOG.md`,
  `VERSION` 0.1.0.
- Механика правил: CI (ruff, pytest на живом PostGIS, `makemigrations --check`,
  сверка status.md с веткой, сверка `.env.example`), шаблон PR,
  pre-commit хук против коммитов в `main`, ruleset на GitHub.
- `scripts/check_env_example.py` при первом запуске нашёл три
  незадокументированные переменные — добавлены в `.env.example`.

## Now

- Ветка `docs/repo-contract` готова к PR. Код приложений не менялся:
  бизнес-логика по-прежнему заглушки с `NotImplementedError`.

## Next

- Этап 1, первый шаг: API постановки отметки без регистрации
  (`apps/sightings`) — сериализатор, вьюха, рейтлимит, тесты на
  `author IS NULL` / `report IS NULL`.

## Resume

1. `git fetch && git checkout docs/repo-contract && git pull`
2. `make hooks && make up && make migrate`
3. `make lint && make test`
4. Смёржить PR, затем начать `feat/sighting-api` от свежего `main`.

## Open

- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- Поставщик тайлов не выбран (своя сборка или Яндекс/2ГИС).
