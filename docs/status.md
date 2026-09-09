# Status

Updated: 2026-09-09
Stage: 1 (ядро)
Step: механические гарантии контракта; код этапа 1 ещё не начат
Branch: `chore/flow-guards`
PR: #1 (контракт) + #2 (эта ветка, поверх #1)
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

- PR #1 (`docs/repo-contract`) зелёный, ждёт мержа.
- Ветка `chore/flow-guards` поверх него: инвариантные тесты, `pre-push`,
  `make session-start`, Dependabot, required status checks. После мержа #1
  GitHub перенацелит PR #2 на `main`.
- Код приложений не менялся: бизнес-логика по-прежнему заглушки
  с `NotImplementedError`.

## Next

- Этап 1, первый шаг: API постановки отметки без регистрации
  (`apps/sightings`) — сериализатор, вьюха, рейтлимит, тесты на
  `author IS NULL` / `report IS NULL`.

## Resume

1. `git fetch && git checkout chore/flow-guards && git pull`
2. `make hooks && make up && make migrate`
3. `make session-start && make check`
4. Смёржить #1, затем #2, затем начать `feat/sighting-api` от свежего `main`.

## Open

- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- Поставщик тайлов не выбран (своя сборка или Яндекс/2ГИС).
