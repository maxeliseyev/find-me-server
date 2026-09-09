# Git workflow

До первой версии в проде работаем с **одной** долгоживущей веткой `main`.
Ветку `develop` не заводим. Решение и триггер смены: `decisions/git-trunk-until-v1.md`.

---

## Сейчас (до v1)

```
main  ← единственная интеграция, всегда зелёная
  ↑
  PR (squash)
  ↑
feat/sighting-api   fix/fanout-quiet-hours   docs/agents-md   chore/ci
```

1. Обновить `main`: `git checkout main && git pull`.
2. Ветка от актуального `main`: `feat/…`, `fix/…`, `chore/…`, `docs/…`, `test/…`.
3. Коммиты — Conventional Commits (`feat(sightings): …`).
4. Открыть PR **в `main`**. Прямой пуш в `main` запрещён, включая автора репо;
   на GitHub это закрыто ruleset'ом, локально — pre-commit хуком (`make hooks`).
5. Зелёный CI: джобы `lint`, `test`, `contract` обязательны для мержа
   (required status checks в ruleset). Definition of done — в `AGENTS.md`.
6. Ревью: если второго человека на PR нет, self-merge допустим с пометкой в
   описании (`self-merge: <причина>`).
7. Merge: **squash**. История `main` = один шаг / один фикс на коммит.
8. Удалить ветку после merge.

`pre-push` гоняет `make check` до отправки ветки: ruff, сверку `status.md` и
`.env.example`, `makemigrations --check` и тесты, если PostGIS поднят. Ошиблись —
чините, а не `--no-verify`: обход допустим в исключительном случае и объясняется
в описании PR.

Зависимости и экшены обновляет Dependabot раз в месяц (`chore(deps)`,
`chore(ci)`). Мажорную линию Django он не тронет: она закреплена в `pyproject.toml`.

Незаконченная сессия: push ветки (хотя бы draft PR) и имя ветки в `status.md`.
Local working tree второй человек не подхватит.

### Имена веток

| Префикс | Когда |
|---|---|
| `feat/` | Шаг плана или новая возможность (`feat/sighting-api`) |
| `fix/` | Баг на уже слитом поведении |
| `test/` | Только тесты |
| `docs/` | Документация, AGENTS, ADR, спека |
| `chore/` | Зависимости, CI, docker, настройки |

Имя короткое, латиница, без номера PR в названии.

### PR

- Один PR = один шаг этапа или один связный фикс.
- В описании: зачем, как проверить, какие инварианты `AGENTS.md` задеты.
- Не смешивать модель данных, API и бота в одном PR.
- Не тащить bump Django, реформат дерева и фичу вместе.

### Если случайно закоммитил в `main`

```bash
git branch feat/<тема>          # запомнить работу
git reset --hard origin/main    # вернуть main к удалённому состоянию
git checkout feat/<тема>
```

Пуш всё равно не пройдёт: ruleset запрещает запись в `main` мимо PR.

---

## После первой версии в проде

Когда сервис работает на пилотном районе и им пользуются:

1. Пометить `main`: `v1.0.0`.
2. Завести `develop` от этого тега; новая работа `feat/*` → PR в **`develop`**.
3. `main` = то, что развёрнуто. Хотфикс: `hotfix/…` от `main` → PR в `main`
   → тег `v1.0.x` → merge в `develop`.
4. Релиз следующей линии: `develop` → `main`, тег.

До этого шага имитировать Git Flow незачем: `develop` будет вторым `main`
без пользователей на первом.

Эту секцию не включать в CI и настройки заранее. Дойдёте до v1 — обновить
этот файл, `AGENTS.md` и ruleset в одном PR.
