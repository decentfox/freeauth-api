path := ./

define Comment
	- Run `make help` to see all the available options.
	- Run `make setup` to run first-time project setup.
	- Run `make lint` to run the linter.
endef

.PHONY: help
help: ## Show this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: dep-install
dep-install: ## Install latest versions of prod dependencies
	@echo
	@echo "Installing dependencies..."
	@echo "=========================="
	@poetry install --sync

.PHONY: install-edgedb
install-edgedb: ## Install the EdgeDB CLI
	@echo
	@echo "Installing EdgeDB..."
	@echo "===================="
	@which edgedb > /dev/null 2>&1 || (curl --proto '=https' --tlsv1.2 -sSf https://sh.edgedb.com | sh -s -- -y)

.PHONY: init-project
init-project: ## Initial a new or existing FreeAuth DB project
	@echo
	@echo "Initializing EdgeDB project..."
	@echo "=============================="
	@-edgedb project init --project-dir . 2> /dev/null

.PHONY: up
up: ## Upgrade database to the latest revision
	@echo
	@echo "Upgrading database to the latest revision..."
	@echo "=============================="
	@edgedb migration apply

.PHONY: sync-freeauth
sync-freeauth: up ## Sync FreeAuth dbschema
	@echo
	@echo "Synchronizing FreeAuth dbschema..."
	@echo "=============================="
	@poetry run freeauth-db sync
	@-edgedb migration create --non-interactive 2> /dev/null
	@edgedb migration apply

.PHONY: setup-admin
setup-admin: up ## Setup administrator account.
	@echo
	@echo "Setting up administrator account...."
	@echo "=============================="
	@poetry run freeauth-db admin setup

.PHONY: setup
setup: install-edgedb dep-install init-project sync-freeauth setup-admin ## Run first-time setup
	@echo
	@echo "${Green}All set!${NC} Run \`make dev\` to start a uvicorn dev server on port 5001."

dev: dep-install up
	@poetry run uvicorn app.asgi:fast_api --reload --host 0.0.0.0 --port 5001

.PHONY: lint
lint: isort black flake mypy ## Apply all the linters.

.PHONY: black
black: ## Apply black.
	@echo
	@echo "Applying black..."
	@echo "================="
	@echo
	@poetry run black .
	@echo

.PHONY: isort
isort: ## Apply isort.
	@echo "Applying isort..."
	@echo "================="
	@echo
	@poetry run isort .

.PHONY: flake
flake: ## Apply flake8.
	@echo
	@echo "Applying flake8..."
	@echo "================="
	@echo
	@poetry run flake8 .

.PHONY: mypy
mypy: ## Apply mypy.
	@echo
	@echo "Applying mypy..."
	@echo "================="
	@echo
	@poetry run mypy .
