"""Unit test fixtures — isolated components, no real filesystem structures."""

import pytest

from file_organiser.core.categoriser import FileCategoriser
from file_organiser.core.mover import FileMover, MoveOptions
from file_organiser.core.validators import PathValidator
from file_organiser.plugins.registry import PluginRegistry


@pytest.fixture
def move_options() -> MoveOptions:
    """Create a move options instance.

    Returns:
        MoveOptions instance with default configuration
    """
    return MoveOptions(
        atomic=True,
        verify_checksum=True,
        preserve_metadata=True,
        create_dirs=True,
        overwrite_existing=False,
    )


@pytest.fixture
def file_mover(move_options) -> FileMover:
    """Create a file mover instance.

    Args:
        move_options: MoveOptions instance to configure the mover

    Returns:
        FileMover instance with the given move options
    """
    return FileMover(options=move_options)


@pytest.fixture
def file_categoriser(mock_plugin_registry) -> FileCategoriser:
    """Create a file categoriser instance.

    Args:
        mock_plugin_registry: PluginRegistry instance to configure the categoriser

    Returns:
        FileCategoriser instance with the given plugin registry
    """
    return FileCategoriser(
        plugin_registry=mock_plugin_registry,
        fallback_category="Uncategorised",
    )


@pytest.fixture
def categoriser_with_fallback() -> FileCategoriser:
    """Create a categoriser instance with fallback category.

    Returns:
        FileCategoriser instance with fallback category set to "Other"
    """
    return FileCategoriser(
        plugin_registry=PluginRegistry(),
        fallback_category="Other",
    )


@pytest.fixture
def path_validator() -> type:
    """Create a path validator class.

    Returns:
        PathValidator class
    """
    return PathValidator
