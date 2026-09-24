# Status

Updated: 2026-09-24
Stage: 1 (ядро)
Step: этап 1 — карантин и Celery-публикация фото отметок
Branch: `claude/eloquent-mccarthy-oq9n9c`
PR: none (ветка запушена, PR по запросу)
Blockers: none

## Done

- Скелет слит в `main` коммитом `5bd003a`: Django 5.2 LTS + GeoDjango,
  приложения по модели данных спеки, миграции проверены на PostGIS 3.5,
  Celery, aiogram, docker-compose, ruff, pytest.
- Контракт репозитория и механические гарантии слиты в `main` коммитами
  `b7d4e9b` и `a3b0a0e`.
- Dependabot не может поднимать major/minor Django (`0237a35`).
- API постановки отметки слито в `main` коммитом `a529d63`.
- API карты слито в `main` коммитом `daae2c4`.
- Спецификация v0.2 слита в `main` коммитом `6c69f62`.
- API создания объявления слито в `main` коммитом `7299cce`.
- Безопасная обработка изображения (`apps/core/images.py`) слита в `main`
  коммитом `af8ce58` (#11).

## Now

- На ветке: карантин исходников (`STORAGES["quarantine"]`), статус и
  `exif_geog` у `SightingPhoto` (миграция `sightings/0002`),
  `apps/sightings/services.py` и задача `process_sighting_photo`.
  `make lint` и `make test` (53 passed) зелёные, `makemigrations --check` чистый.
  Почему так — `docs/sessions/2026-09-24-photo-quarantine.md`.

## Next

- Открыть PR с этой ветки и смёржить; затем endpoint загрузки фото к отметке
  поверх `accept_sighting_photo`.

## Resume

1. `git fetch && git checkout claude/eloquent-mccarthy-oq9n9c && git pull`
2. `make hooks && make up && make migrate && make test`
3. Открыть PR в `main`; после мержа — endpoint загрузки фото.

## Open

- Фан-аут уведомлений и пересчёт зоны при новой отметке не подключены:
  задачи Celery ещё заглушки. В `SightingCreateView` стоит TODO с местом вызова.
- Нет уборки зависших `pending`-фото и сирот в карантине — нужна до запуска.
- `PetPhoto` ещё не переведён на карантин.
- Монетизация не выбрана (раздел 12.1 спеки). Решение нужно до конца этапа 1:
  платное продвижение — отдельная подсистема, а не поле в модели.
- Город и район пилота не выбраны; в коде не хардкодятся.
- До выбора пилотного района нужно проверить качество OSM: номера домов и
  контуры зданий (раздел 7.3 спеки).
