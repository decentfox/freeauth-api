install:
	@poetry install
	@poetry run pre-commit install
	@poetry run freeauth-db install 2> /dev/null
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && \
	poetry install)

lint:
	@poetry run isort src tests
	@poetry run black src tests
	@poetry run flake8 src tests
	@poetry run mypy src tests
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-ext/fastapi-ext && make lint)
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make lint)

testdb:
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make testdb)

test:
	@poetry run pytest
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-ext/fastapi-ext && make test)
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make test)

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

dev:
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && \
	make dev)

genqlapi: up
	@for target in async blocking; do \
		for module in admin auth; do \
			target_name=$$(if [ "$$target" = "async" ]; then echo "_async"; else echo ""; fi); \
			file_path="src/freeauth/db/$${module}/$${module}_qry$${target_name}_edgeql.py"; \
			command="poetry run edgedb-py -I FreeAuth --target $$target --dir src/freeauth/db/$$module --file $$file_path"; \
			$$command; \
		done \
	done
