"""Pytest configuration and shared fixtures for all tests."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from fixtures.mock_plugins import (
    MockCategorisationPlugin,
    MockFilterPlugin,
    MockPostProcessingPlugin,
    MockReporterPlugin,
)
from fixtures.sample_files import create_sample_files

from file_organiser.core.models import FileInfo, MoveResult, MoveStatus
from file_organiser.plugins.registry import PluginRegistry


@pytest.fixture
def tmp_unorganised_dir(tmp_path: Path) -> Path:
    """Create a temporary unorganised directory with various files.

    Returns:
        Path to the unorganised directory
    """
    source_dir = tmp_path / "unorganised"
    source_dir.mkdir()
    create_sample_files(
        source_dir,
        [
            ("document.txt", "This is a document"),
            ("report.pdf", "%PDF-1.4\nFake PDF"),
            ("image.png", "\x89PNG\r\n\x1a\n"),
            ("video.mp4", "ftypisom"),
            ("script.py", "print('hello')"),
            ("archive.zip", "PK\x03\x04"),
        ],
    )
    return source_dir


@pytest.fixture
def sample_text_file_info() -> FileInfo:
    """Create a sample text file info.

    Returns:
        FileInfo instance for a text file
    """
    return FileInfo(
        path=Path("document.txt"),
        name="document.txt",
        extension=".txt",
        size=100,
        modified_time=0,
    )


@pytest.fixture
def sample_code_file_info() -> FileInfo:
    """Create a sample code file info.

    Returns:
        FileInfo instance for a code file
    """
    return FileInfo(
        path=Path("script.py"),
        name="script.py",
        extension=".py",
        size=500,
        modified_time=0,
    )


@pytest.fixture
def sample_image_file_info() -> FileInfo:
    """Create a sample image file info.

    Returns:
        FileInfo instance for an image file
    """
    return FileInfo(
        path=Path("photo.jpg"),
        name="photo.jpg",
        extension=".jpg",
        size=2000,
        modified_time=0,
    )


@pytest.fixture
def sample_video_file_info() -> FileInfo:
    """Create a sample video file info.

    Returns:
        FileInfo instance for a video file
    """
    return FileInfo(
        path=Path("movie.mp4"),
        name="movie.mp4",
        extension=".mp4",
        size=50000000,
        modified_time=0,
    )


@pytest.fixture
def various_file_infos() -> list[FileInfo]:
    """Create a list of various file infos.

    Returns:
        List of FileInfo instances
    """
    return [
        FileInfo(Path("doc.txt"), "doc.txt", ".txt", 100, 0),
        FileInfo(Path("code.py"), "code.py", ".py", 500, 0),
        FileInfo(Path("image.jpg"), "image.jpg", ".jpg", 2000, 0),
        FileInfo(Path("video.mp4"), "video.mp4", ".mp4", 50000000, 0),
        FileInfo(Path("archive.zip"), "archive.zip", ".zip", 5000, 0),
    ]


@pytest.fixture
def successful_move_result() -> MoveResult:
    """Create a successful move result.

    Returns:
        MoveResult with SUCCESS status
    """
    return MoveResult(
        status=MoveStatus.SUCCESS,
        source=Path("source.txt"),
        destination=Path("dest/source.txt"),
        category="Documents",
    )


@pytest.fixture
def failed_move_result() -> MoveResult:
    """Create a failed move result.

    Returns:
        MoveResult with FAILED status
    """
    return MoveResult(
        status=MoveStatus.FAILED,
        source=Path("source.txt"),
        destination=None,
        error=Exception("Permission denied"),
    )


@pytest.fixture
def skipped_move_result() -> MoveResult:
    """Create a skipped move result.

    Returns:
        MoveResult with SKIPPED status
    """
    return MoveResult(
        status=MoveStatus.SKIPPED, source=Path("source.txt"), destination=None
    )


@pytest.fixture
def dry_run_move_result() -> MoveResult:
    """Create a dry run move result.

    Returns:
        MoveResult with DRY_RUN status
    """
    return MoveResult(
        status=MoveStatus.DRY_RUN,
        source=Path("source.txt"),
        destination=Path("dest/source.txt"),
        category="Documents",
    )


@pytest.fixture
def test_config() -> dict:
    """Create a test config dictionary.

    Returns:
        Dictionary containing test configuration
    """
    return {
        "atomic": True,
        "verify_checksum": True,
        "preserve_metadata": True,
        "create_dirs": True,
        "include_hidden": False,
        "validate_paths": True,
    }


@pytest.fixture
def mock_categoriser_plugin() -> MockCategorisationPlugin:
    """Create a mock categorisation plugin.

    Returns:
        MockCategorisationPlugin instance
    """
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
    """Create a mock filter plugin.

    Returns:
        MockFilterPlugin instance
    """
    return MockFilterPlugin(name="test_filter", exclude_all=False)


@pytest.fixture
def mock_reporter_plugin() -> MockReporterPlugin:
    """Create a mock reporter plugin.

    Returns:
        MockReporterPlugin instance
    """
    return MockReporterPlugin(name="test_reporter")


@pytest.fixture
def mock_post_processor_plugin() -> MockPostProcessingPlugin:
    """Create a mock post-processing plugin.

    Returns:
        MockPostProcessingPlugin instance
    """
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
    """Create a failing mock categoriser plugin.

    Returns:
        MockCategorisationPlugin instance that will fail
    """
    return MockCategorisationPlugin(name="failing_categoriser", should_fail=True)
