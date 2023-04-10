install:
	poetry install --sync

format:
	poetry run isort src
	poetry run black src

lint: format
	poetry run isort src --check
	poetry run flake8 src
	poetry run mypy src
	poetry run black src --check

test:
	poetry run pytest src
