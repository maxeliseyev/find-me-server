.PHONY: install hooks up down migrate mm run worker beat bot shell test lint fmt \
        superuser check status-check env-check version session-start

install:            ## Поставить зависимости
	uv sync --all-extras

hooks:              ## Включить git-хуки репозитория (запрет коммитов в main)
	git config core.hooksPath scripts/git-hooks
	@echo "hooks: scripts/git-hooks"

up:                 ## Поднять postgis + redis
	docker compose up -d db redis

down:
	docker compose down

migrate:
	uv run python manage.py migrate

mm:                 ## makemigrations
	uv run python manage.py makemigrations

run:
	uv run python manage.py runserver

worker:
	uv run celery -A config worker -l info

beat:
	uv run celery -A config beat -l info

bot:
	uv run --extra bot python -m bot.main

shell:
	uv run python manage.py shell_plus

superuser:
	uv run python manage.py createsuperuser

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format . && uv run ruff check --fix .

status-check:       ## Сверить docs/status.md с текущей веткой
	uv run python scripts/check_status.py

env-check:          ## Проверить, что настройки описаны в .env.example
	uv run python scripts/check_env_example.py

check: lint status-check env-check test  ## Всё, что гоняет CI
	uv run python manage.py makemigrations --check --dry-run

version:
	@cat VERSION

session-start:      ## Ритуал старта сессии: ветка, PR, docs/status.md
	@uv run python scripts/session_start.py
