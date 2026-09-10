# Status

Updated: 2026-09-10
Stage: 1 (ядро)
Step: этап 1 — выдача карты
Branch: `feat/map-api`
PR: https://github.com/maxeliseyev/find-me-server/pull/8 (draft)
Blockers: none

## Done

- Скелет слит в `main` коммитом `5bd003a`: Django 5.2 LTS + GeoDjango,
  приложения по модели данных спеки, миграции проверены на PostGIS 3.5,
  Celery, aiogram, docker-compose, ruff, pytest.
- Контракт репозитория и механические гарантии слиты в `main` коммитами
  `b7d4e9b` и `a3b0a0e`.
- Dependabot не может поднимать major/minor Django (`0237a35`).
- API постановки отметки слито в `main` коммитом `a529d63`:
  `apps/sightings/{serializers,views,throttling,urls}.py`, 10 тестов API
  и два инвариантных теста (1 — анонимная отметка, 12 — рейтлимит).

## Now

- Draft PR #8: реализована и проверена выдача активных объявлений и видимых
  отметок в bbox с серверной кластеризацией. `make lint` и `make test` зелёные.

## Next

- Этап 1, следующий шаг: API создания активного объявления о пропаже.

## Resume

1. `git fetch && git checkout feat/map-api && git pull`
2. `make hooks && make up && make migrate`
3. Проверить и смёржить #8; после merge создать `feat/report-api` от свежего `main`.

## Open

- Фан-аут уведомлений и пересчёт зоны при новой отметке не подключены:
  задачи Celery ещё заглушки. В `SightingCreateView` стоит TODO с местом вызова.
- Загрузка фото к отметке (и срезка EXIF) — отдельный шаг, в этом API нет.
- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- Поставщик тайлов не выбран (своя сборка или Яндекс/2ГИС).
