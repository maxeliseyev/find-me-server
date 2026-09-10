# Status

Updated: 2026-09-10
Stage: 1 (ядро)
Step: гигиена Dependabot перед стартом кода этапа 1
Branch: `chore/dependabot-guard`
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

- PR #1 (`b7d4e9b`) и PR #2 (`a3b0a0e`) смёржены в `main`: контракт
  репозитория и его механические гарантии.
- Dependabot отработал первым же прогоном и предложил Django 6.1 — с правкой
  границы `<5.3` в `pyproject.toml`. Запрещено явным `ignore` в
  `.github/dependabot.yml`; PR закрыт.
- Открыты PR #3 и #4 от Dependabot на экшены — рутина, ждут проверки CI.
- Код приложений не менялся: бизнес-логика по-прежнему заглушки
  с `NotImplementedError`.

## Next

- Этап 1, первый шаг: API постановки отметки без регистрации
  (`apps/sightings`) — сериализатор, вьюха, рейтлимит, тесты на
  `author IS NULL` / `report IS NULL`.

## Resume

1. `git fetch && git checkout chore/dependabot-guard && git pull`
2. `make hooks && make up && make migrate`
3. `make session-start && make check`
4. Смёржить этот PR и #3/#4, затем `feat/sighting-api` от свежего `main`.

## Open

- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- Поставщик тайлов не выбран (своя сборка или Яндекс/2ГИС).
