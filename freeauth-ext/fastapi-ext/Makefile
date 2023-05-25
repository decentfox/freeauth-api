install:
	@poetry install
	@poetry run pre-commit install

lint:
	@poetry run isort .
	@poetry run black .
	@poetry run flake8 .
	@poetry run mypy .

test:
	@poetry run pytest
