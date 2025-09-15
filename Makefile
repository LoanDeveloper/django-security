ENV_FILE?=.env

.PHONY: up build down logs shell migrate seed superuser dev test lint fmt

up:
	docker compose --env-file $(ENV_FILE) up -d --build

down:
	docker compose down

logs:
	docker compose logs -f web | cat

shell:
	docker compose exec web sh -lc "python manage.py shell"

migrate:
	docker compose exec web sh -lc "python manage.py migrate"

seed:
	docker compose exec web sh -lc "python manage.py seed_demo"

superuser:
	docker compose exec web sh -lc "python manage.py createsuperuser"

dev:
	docker compose exec web sh -lc "python manage.py runserver 0.0.0.0:8000"

test:
	docker compose exec web sh -lc "pytest -q"

lint:
	docker compose exec web sh -lc "ruff check . && black --check ."

fmt:
	docker compose exec web sh -lc "ruff check . --fix && black ."


