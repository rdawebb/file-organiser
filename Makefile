.PHONY: install install-dev lint format test test-cov clean

install:
	uv pip install -e .

install-dev:
	uv sync --all-extras
	uv pip install -e .

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

test:
	uv run pytest tests/

test-cov:
	uv run pytest --cov=src tests/

clean:
	uv run scripts/clean.py