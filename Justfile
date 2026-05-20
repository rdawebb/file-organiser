# Install in editable mode
install:
	uv pip install -e .

# Install development dependencies
install-dev:
	uv sync --all-extras
	uv run scripts/build_rust.py

# Lint code
lint:
	uv run ruff check --fix src tests

# Format code
format:
	uv run ruff format src tests scripts

# Type check code
type:
	uv run ty check src tests

# Code quality checks
check:
	uv run ruff check --fix src tests
	uv run ruff format src tests scripts
	uv run ty check src tests

# Run all Python tests
test-py:
	uv run pytest -v tests/

# Run all Python tests with coverage
test-cov:
	uv run pytest --cov=src tests/

# Run all Rust tests
test-rust:
	uv run scripts/test_rust.py

# Run all tests
test:
	uv run scripts/test_rust.py
	uv run pytest -v tests/

# Clean up temporary files
clean:
	uv run scripts/clean.py
