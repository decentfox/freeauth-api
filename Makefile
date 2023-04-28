install:
	poetry install --sync
	poetry run pre-commit install

lint:
	poetry run isort src
	poetry run black src
	poetry run flake8 src
	poetry run mypy src

test:
	poetry run pytest --reset-db

resetdb:
	edgedb query "create database tmp"
	edgedb -d tmp query "drop database edgedb" "create database edgedb"
	edgedb query "drop database tmp"
	edgedb migrate

db:
	edgedb migration create

up:
	edgedb migrate

dev: install up
	poetry run uvicorn freeauth.asgi:app --reload --host 0.0.0.0 --port 5001

genqlapi:
	poetry run edgedb-py --file src/freeauth/query_api.py
