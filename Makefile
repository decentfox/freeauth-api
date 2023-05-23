install:
	@git submodule init
	@git submodule update
	@(cd extensions/freeauth && make install)
	@poetry install --sync
	@poetry run pre-commit install
	@poetry run freeauth-db install 2> /dev/null

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
	@if test -n "$$(find src/freeauth/admin -name '*.edgeql' -type f)"; then \
		cd src/freeauth/admin && \
		poetry run edgedb-py -I FreeAuth --file query_api.py; \
	else \
	  	echo "No .edgeql files found, skip to generate query API."; \
	fi
