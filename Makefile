install:
	poetry install --sync

lint:
	poetry run isort src
	poetry run black src
	poetry run flake8 src
	poetry run mypy src

test:
	poetry run pytest src

dev: install
	poetry run uvicorn freeauth.asgi:app --reload --host 0.0.0.0 --port 5001
