install:
	@poetry install
	@poetry run pre-commit install

lint:
	@poetry run isort .
	@poetry run black .
	@poetry run flake8 .
	@poetry run mypy --ignore-missing-imports .

testdb:
	@poetry run pytest --reset-db

test:
	@poetry run pytest -s

up:
	@poetry run freeauth-db migration apply

env:
	@test -f .env || touch .env
	@grep -qE "^\s*FREEAUTH_APP_ID\s*=" .env || echo "FREEAUTH_APP_ID=$$(edgedb -I FreeAuth query 'select assert_single(freeauth::Application.id filter freeauth::Application.is_protected)')" >> .env

dev: install up env
	@poetry run uvicorn freeauth.admin.asgi:app --reload --host 0.0.0.0 --port 5001
