# Install in editable mode
install:
	uv pip install -e .

# Install development dependencies
install-dev:
	uv sync --all-extras
	uv pip install -e .

# Lint code
lint:
	uv run ruff check --fix src tests

# Format code
format:
	uv run ruff format src tests scripts

type:
	uv run ty check src tests

# Run all tests
test:
	uv run pytest -v tests/

# Run all tests with coverage
test-cov:
	uv run pytest --cov=src tests/

# Clean up temporary files
clean:
	uv run scripts/clean.py
