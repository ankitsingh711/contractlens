.PHONY: up down build logs api-shell web-shell migrate revision test-api test-web lint-api lint-web typecheck-web

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

api-shell:
	docker compose exec api sh

web-shell:
	docker compose exec web sh

migrate:
	cd apps/api && . .venv/bin/activate && alembic upgrade head

revision:
	cd apps/api && . .venv/bin/activate && alembic revision --autogenerate -m "$(m)"

test-api:
	cd apps/api && . .venv/bin/activate && python -m pytest tests/ -v

test-web:
	cd apps/web && npm test

lint-api:
	cd apps/api && . .venv/bin/activate && ruff check app tests

lint-web:
	cd apps/web && npm run lint

typecheck-web:
	cd apps/web && npx tsc --noEmit
