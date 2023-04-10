install:
	poetry install --sync

lint:
	poetry run isort src
	poetry run flake8 src
	poetry run mypy src
	poetry run black src

test:
	poetry run pytest src
