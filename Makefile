install: extensions/*/pyproject.toml
	@(cd extensions/freeauth && make install)
	@poetry install --sync
	@poetry run pre-commit install

lint:
	@poetry run isort src
	@poetry run black src
	@poetry run flake8 src
	@poetry run mypy src

testdb:
	@poetry run pytest --reset-db

test:
	@poetry run pytest -s

resetdb:
	@edgedb query "drop database tmp"
	@edgedb query "create database tmp"
	@edgedb -d tmp query "drop database edgedb" "create database edgedb"
	@edgedb query "drop database tmp"
	@edgedb restore local_data.dump

db:
	@edgedb dump local_data.dump
	@freeauth-db migration create

up:
	@freeauth-db migration apply

dev: install up
	@poetry run uvicorn freeauth.admin.asgi:app --reload --host 0.0.0.0 --port 5001

genqlapi:
	@(cd src/freeauth/admin && poetry run edgedb-py --file query_api.py)

extensions/*/pyproject.toml:
	@git submodule init
	@git submodule update
