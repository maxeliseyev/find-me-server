# Status

Updated: 2026-09-10
Stage: 1 (ядро)
Step: этап 1 — API постановки отметки
Branch: `feat/sighting-api`
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

- PR #1 (`b7d4e9b`) и PR #2 (`a3b0a0e`) смёржены: контракт репозитория
  и его механические гарантии.
- PR #6 (`chore/dependabot-guard`) открыт: Dependabot предложил Django 6.1,
  правя границу `<5.3` в `pyproject.toml`; запрет добавлен, его PR закрыт.
- На этой ветке: первый рабочий код этапа 1 — постановка отметки.
  `apps/sightings/{serializers,views,throttling,urls}.py`, 10 тестов API
  и два инвариантных теста (1 — анонимная отметка, 12 — рейтлимит).

## Next

- Этап 1, следующий шаг: выдача для карты — активные объявления и видимые
  отметки в bbox, кластеризация на сервере, публичная точка объявления
  через `public_geog`.

## Resume

1. `git fetch && git checkout feat/sighting-api && git pull`
2. `make hooks && make up && make migrate`
3. `make session-start && make check`
4. Смёржить #6 и этот PR (ветку переносить `rebase --onto`, не «Update branch»),
   затем `feat/map-api` от свежего `main`.

## Open

- Фан-аут уведомлений и пересчёт зоны при новой отметке не подключены:
  задачи Celery ещё заглушки. В `SightingCreateView` стоит TODO с местом вызова.
- Загрузка фото к отметке (и срезка EXIF) — отдельный шаг, в этом API нет.
- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- Поставщик тайлов не выбран (своя сборка или Яндекс/2ГИС).
