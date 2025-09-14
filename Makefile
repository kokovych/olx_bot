.PHONY: install lint format typecheck pre-commit

# Install dependencies and setup pre-commit hooks
install:
	poetry install
	poetry run pre-commit install

# Run linters and checks (flake8, black, isort, mypy)
lint:
	poetry run black --check src tests alembic
	poetry run isort --check-only src tests alembic
	poetry run flake8 src tests alembic
	poetry run mypy src tests

# Automatically format code with black and isort
format:
	poetry run black src tests alembic
	poetry run isort src tests alembic

# Run static type checking
typecheck:
	poetry run mypy src tests

# Run pre-commit hooks on all files
pre-commit:
	poetry run pre-commit run --all-files
