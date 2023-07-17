path := ./

define Comment
	- Run `make help` to see all the available options.
endef

.PHONY: help
help: ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: dep-install
dep-install: ## Install latest versions of prod dependencies.
	@echo
	@echo "Installing dependencies..."
	@echo "=========================="
	@poetry install
	@poetry run pre-commit install
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && \
	make install)

.PHONY: install-edgedb
install-edgedb: ## Install the EdgeDB CLI.
	@echo
	@echo "Installing EdgeDB..."
	@echo "===================="
	@which edgedb > /dev/null 2>&1 || (curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh -s -- -y)

.PHONY: init-project
init-project: ## Initial a new or existing FreeAuth DB project.
	@echo
	@echo "Initializing EdgeDB project..."
	@echo "=============================="
	@-edgedb project init --project-dir . 2> /dev/null

.PHONY: db
db: ## Create a db migration.
	@echo
	@echo "Creating a migration..."
	@edgedb dump local_data.dump
	@edgedb migration create

.PHONY: up
up: ## Upgrade database to the latest revision.
	@echo
	@echo "Upgrading database to the latest revision..."
	@echo "=============================="
	@edgedb migration apply

.PHONY: genqlapi
genqlapi: up ## Generate query APIs.
	@for target in async blocking; do \
		for module in admin auth; do \
			target_name=$$(if [ "$$target" = "async" ]; then echo "_async"; else echo ""; fi); \
			file_path="src/freeauth/db/$${module}/$${module}_qry$${target_name}_edgeql.py"; \
			command="poetry run edgedb-py --target $$target --dir src/freeauth/db/$$module --file $$file_path"; \
			$$command; \
		done \
	done

.PHONY: sync-freeauth
sync-freeauth: up ## Sync FreeAuth dbschema.
	@echo
	@echo "Synchronizing FreeAuth dbschema..."
	@echo "=============================="
	@poetry run freeauth-db sync
	@-edgedb migration create --non-interactive 2> /dev/null
	@edgedb migration apply

.PHONY: setup-admin
setup-admin: ## Setup administrator account.
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && \
	make setup)

.PHONY: setup
setup: install-edgedb dep-install init-project sync-freeauth setup-admin ## Setup environment, run first-time setup.
	@echo
	@echo "${Green}All set!${NC} Run \`make dev\` to start a uvicorn dev server on port 5001."

.PHONY: dev
dev: ## Run FreeAuth admin server in dev mode.
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && \
	make dev)

.PHONY: lint
lint: isort black flake mypy ## Apply all the linters.
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-ext/fastapi-ext && make lint)
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make lint)

.PHONY: black
black: ## Apply black.
	@echo
	@echo "Applying black..."
	@echo "================="
	@echo
	@poetry run black src tests

.PHONY: isort
isort: ## Apply isort.
	@echo
	@echo "Applying isort..."
	@echo "================="
	@echo
	@poetry run isort src tests

.PHONY: flake
flake: ## Apply flake8.
	@echo
	@echo "Applying flake8..."
	@echo "================="
	@echo
	@poetry run flake8 src tests

.PHONY: mypy
mypy: ## Apply mypy.
	@echo
	@echo "Applying mypy..."
	@echo "================="
	@echo
	@poetry run mypy src tests

.PHONY: test
test: ## Run unit tests.
	@echo
	@poetry run pytest
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-ext/fastapi-ext && make test)
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make test)

.PHONY: testdb
testdb: ## Reset test DB before running tests (if any schema changes).
	@(source $$(poetry env info --path)/bin/activate && \
	cd freeauth-admin && make testdb)

.PHONY: resetdb
resetdb: ## Restore current DB from a dumped file.
	@edgedb query "create database tmp"
	@edgedb -d tmp query "drop database edgedb" "create database edgedb"
	@edgedb query "drop database tmp"
	@edgedb restore local_data.dump
