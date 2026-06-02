"""Integration test fixtures — full filesystem structures for end-to-end tests."""

from pathlib import Path

import pytest
from fixtures.directories import create_organised_directory
from fixtures.sample_files import create_problematic_files, create_test_structure


@pytest.fixture
def tmp_organised_dir(tmp_path: Path) -> dict:
    """Create a temporary organised directory structure.

    Args:
        tmp_path: Path to the temporary directory

    Returns:
        Dictionary representing the organised directory structure
    """
    return create_organised_directory(tmp_path / "organised")


@pytest.fixture
def tmp_problematic_files(tmp_path: Path) -> dict:
    """Create a temporary directory with problematic files.

    Args:
        tmp_path: Path to the temporary directory

    Returns:
        Dictionary representing the problematic files
    """
    return create_problematic_files(tmp_path / "problematic")


@pytest.fixture
def test_structure(tmp_path: Path) -> dict:
    """Create a test structure in the temporary directory.

    Args:
        tmp_path: Path to the temporary directory

    Returns:
        Dictionary representing the test structure
    """
    return create_test_structure(tmp_path)
