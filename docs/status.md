# Status

Updated: 2026-09-10
Stage: 1 (ядро)
Step: спецификация v0.2
Branch: `docs/spec-v0-2`
PR: https://github.com/maxeliseyev/find-me-server/pull/9 (draft)
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
- API карты слито в `main` коммитом `daae2c4`: GeoJSON-выдача по bbox,
  серверная кластеризация и публичная точка объявления.

## Now

- Draft PR #9: уточнены стек карты, геокодинг и Telegram как канал создания
  отметки; добавлены два ADR. `make lint` и `make test` зелёные.

## Next

- Проверить и смёржить draft PR #9.

## Resume

1. `git fetch && git checkout docs/spec-v0-2 && git pull`
2. `make hooks && make up && make migrate`
3. Проверить и смёржить #9; затем создать `feat/report-api`.

## Open

- Фан-аут уведомлений и пересчёт зоны при новой отметке не подключены:
  задачи Celery ещё заглушки. В `SightingCreateView` стоит TODO с местом вызова.
- Загрузка фото к отметке (и срезка EXIF) — отдельный шаг, в этом API нет.
- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- До выбора пилотного района нужно проверить качество OSM: номера домов и
  контуры зданий (раздел 7.3 спеки).
