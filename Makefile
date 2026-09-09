.PHONY: install up down migrate mm run worker beat bot shell test lint fmt superuser

install:            ## Поставить зависимости
	uv sync --all-extras

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
