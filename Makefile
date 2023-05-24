install:
	@poetry install
	@(cd freeauth-admin && poetry install)
	@poetry run pre-commit install
	@poetry run freeauth-db install 2> /dev/null

lint:
	@poetry run isort .
	@poetry run black .
	@poetry run flake8 .
	@poetry run mypy .

testdb:
	@(cd freeauth-admin && poetry run pytest --reset-db)

test:
	@poetry run pytest -s
	@(cd freeauth-admin && poetry run pytest -s)

resetdb:
	@edgedb -I FreeAuth query "create database tmp"
	@edgedb -I FreeAuth -d tmp query "drop database edgedb" "create database edgedb"
	@edgedb -I FreeAuth query "drop database tmp"
	@edgedb -I FreeAuth restore local_data.dump

db:
	@edgedb -I FreeAuth dump local_data.dump
	@poetry run freeauth-db migration create

up:
	@poetry run freeauth-db migration apply

dev: install up
	@poetry run uvicorn freeauth.admin.asgi:app --reload --host 0.0.0.0 --port 5001

genqlapi:
	@(cd src/freeauth/db/admin && \
	poetry run edgedb-py -I FreeAuth --target async --file admin_qry_async_edgeql.py && \
	poetry run edgedb-py -I FreeAuth --target blocking --file admin_qry_edgeql.py)
	@(cd src/freeauth/db/auth && \
	poetry run edgedb-py -I FreeAuth --target async --file auth_qry_async_edgeql.py && \
	poetry run edgedb-py -I FreeAuth --target blocking --file auth_qry_edgeql.py)
