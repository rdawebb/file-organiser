"""Pytest configuration and shared fixtures for all tests."""

import pytest
from pathlib import Path

from src.file_organiser.core.models import FileInfo, MoveStatus, MoveResult
from src.file_organiser.core.categoriser import FileCategoriser
from src.file_organiser.core.mover import FileMover, MoveOptions
from src.file_organiser.core.validators import PathValidator
from src.file_organiser.plugins.registry import PluginRegistry

from tests.fixtures.sample_files import (
    create_sample_files,
    create_test_structure,
    create_problematic_files,
)
from tests.fixtures.directories import create_organised_directory
from tests.fixtures.mock_plugins import (
    MockCategorisationPlugin,
    MockFilterPlugin,
    MockReporterPlugin,
    MockPostProcessingPlugin,
)


@pytest.fixture
def tmp_unorganised_dir(tmp_path: Path) -> Path:
    """Create a temporary unorganised directory with various files.

    Yields:
        Path to the unorganised directory
    """
    source_dir = tmp_path / "unorganised"
    source_dir.mkdir()

    files = [
        ("document.txt", "This is a document"),
        ("report.pdf", "%PDF-1.4\nFake PDF"),
        ("image.png", "\x89PNG\r\n\x1a\n"),
        ("video.mp4", "ftypisom"),
        ("script.py", "print('hello')"),
        ("archive.zip", "PK\x03\x04"),
    ]

    create_sample_files(source_dir, files)
    return source_dir


@pytest.fixture
def tmp_organised_dir(tmp_path: Path) -> dict:
    """Create a temporary organised directory with category folders.

    Returns:
        Dictionary with category folder paths
    """
    return create_organised_directory(tmp_path / "organised")


@pytest.fixture
def tmp_problematic_files(tmp_path: Path) -> dict:
    """Create temporary files with problematic names for edge case testing.

    Returns:
        Dictionary with paths to problematic files
    """
    return create_problematic_files(tmp_path / "problematic")


@pytest.fixture
def test_structure(tmp_path: Path) -> dict:
    """Create a complete test directory structure with various file types.

    Returns:
        Dictionary with paths to various file type groups
    """
    return create_test_structure(tmp_path)


@pytest.fixture
def sample_text_file_info() -> FileInfo:
    """Create a sample text file info."""
    return FileInfo(
        path=Path("document.txt"),
        name="document.txt",
        extension=".txt",
        size=100,
        modified_time=0,
    )


@pytest.fixture
def sample_code_file_info() -> FileInfo:
    """Create a sample code file info."""
    return FileInfo(
        path=Path("script.py"),
        name="script.py",
        extension=".py",
        size=500,
        modified_time=0,
    )


@pytest.fixture
def sample_image_file_info() -> FileInfo:
    """Create a sample image file info."""
    return FileInfo(
        path=Path("photo.jpg"),
        name="photo.jpg",
        extension=".jpg",
        size=2000,
        modified_time=0,
    )


@pytest.fixture
def sample_video_file_info() -> FileInfo:
    """Create a sample video file info."""
    return FileInfo(
        path=Path("movie.mp4"),
        name="movie.mp4",
        extension=".mp4",
        size=50000000,
        modified_time=0,
    )


@pytest.fixture
def various_file_infos() -> list[FileInfo]:
    """Create a list of various file infos."""
    return [
        FileInfo(Path("doc.txt"), "doc.txt", ".txt", 100, 0),
        FileInfo(Path("code.py"), "code.py", ".py", 500, 0),
        FileInfo(Path("image.jpg"), "image.jpg", ".jpg", 2000, 0),
        FileInfo(Path("video.mp4"), "video.mp4", ".mp4", 50000000, 0),
        FileInfo(Path("archive.zip"), "archive.zip", ".zip", 5000, 0),
    ]


@pytest.fixture
def successful_move_result() -> MoveResult:
    """Create a successful move result."""
    return MoveResult(
        status=MoveStatus.SUCCESS,
        source=Path("source.txt"),
        destination=Path("dest/source.txt"),
        category="Documents",
    )


@pytest.fixture
def failed_move_result() -> MoveResult:
    """Create a failed move result."""
    return MoveResult(
        status=MoveStatus.FAILED,
        source=Path("source.txt"),
        destination=None,
        error=Exception("Permission denied"),
    )


@pytest.fixture
def skipped_move_result() -> MoveResult:
    """Create a skipped move result."""
    return MoveResult(
        status=MoveStatus.SKIPPED,
        source=Path("source.txt"),
        destination=None,
    )


@pytest.fixture
def dry_run_move_result() -> MoveResult:
    """Create a dry run move result."""
    return MoveResult(
        status=MoveStatus.DRY_RUN,
        source=Path("source.txt"),
        destination=Path("dest/source.txt"),
        category="Documents",
    )


@pytest.fixture
def mock_categoriser_plugin() -> MockCategorisationPlugin:
    """Create a mock categorisation plugin."""
    return MockCategorisationPlugin(
        name="test_categoriser",
        category_map={
            ".txt": "Documents",
            ".py": "Code",
            ".jpg": "Images",
            ".mp4": "Videos",
            ".zip": "Archives",
        },
    )


@pytest.fixture
def mock_filter_plugin() -> MockFilterPlugin:
    """Create a mock filter plugin."""
    return MockFilterPlugin(name="test_filter", exclude_all=False)


@pytest.fixture
def mock_reporter_plugin() -> MockReporterPlugin:
    """Create a mock reporter plugin."""
    return MockReporterPlugin(name="test_reporter")


@pytest.fixture
def mock_post_processor_plugin() -> MockPostProcessingPlugin:
    """Create a mock post-processing plugin."""
    return MockPostProcessingPlugin(name="test_post_processor")


@pytest.fixture
def mock_plugin_registry(mock_categoriser_plugin) -> PluginRegistry:
    """Create a mock plugin registry with test plugins.

    Args:
        mock_categoriser_plugin: The mock categoriser to register

    Returns:
        PluginRegistry with test plugins
    """
    registry = PluginRegistry()
    registry.register(mock_categoriser_plugin)
    return registry


@pytest.fixture
def failing_categoriser_plugin() -> MockCategorisationPlugin:
    """Create a categoriser plugin that fails."""
    return MockCategorisationPlugin(
        name="failing_categoriser",
        should_fail=True,
    )


@pytest.fixture
def move_options() -> MoveOptions:
    """Create default move options."""
    return MoveOptions(
        atomic=True,
        verify_checksum=True,
        preserve_metadata=True,
        create_dirs=True,
        overwrite_existing=False,
    )


@pytest.fixture
def file_mover(move_options) -> FileMover:
    """Create a file mover instance."""
    return FileMover(options=move_options)


@pytest.fixture
def file_categoriser(mock_plugin_registry) -> FileCategoriser:
    """Create a file categoriser instance.

    Args:
        mock_plugin_registry: The mock plugin registry

    Returns:
        FileCategoriser instance
    """
    return FileCategoriser(
        plugin_registry=mock_plugin_registry,
        fallback_category="Uncategorised",
    )


@pytest.fixture
def categoriser_with_fallback() -> FileCategoriser:
    """Create a file categoriser with fallback only (no plugins)."""
    return FileCategoriser(
        plugin_registry=PluginRegistry(),
        fallback_category="Other",
    )


@pytest.fixture
def test_config() -> dict:
    """Create test configuration."""
    return {
        "atomic": True,
        "verify_checksum": True,
        "preserve_metadata": True,
        "create_dirs": True,
        "include_hidden": False,
        "validate_paths": True,
    }


@pytest.fixture
def path_validator() -> type:
    """Provide the PathValidator class for direct testing."""
    return PathValidator
