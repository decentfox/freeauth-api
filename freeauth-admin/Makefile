install:
	@poetry install
	@poetry run pre-commit install

lint:
	@poetry run isort .
	@poetry run black .
	@poetry run flake8 .
	@poetry run mypy .

testdb:
	@poetry run pytest --reset-db

test:
	@poetry run pytest -s

up:
	@poetry run freeauth-db migration apply

dev: install up
	@poetry run uvicorn freeauth.admin.asgi:app --reload --host 0.0.0.0 --port 5001
