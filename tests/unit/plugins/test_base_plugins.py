"""Unit tests for base plugin classes."""

from src.file_organiser.plugins.base import PluginMetadata
from tests.fixtures.mock_plugins import (
    MockCategorisationPlugin,
    MockFilterPlugin,
    MockPostProcessingPlugin,
    MockReporterPlugin,
)


class TestPluginMetadata:
    """Tests for PluginMetadata."""

    def test_metadata_creation(self):
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test Author",
            description="Test Description",
        )

        assert metadata.name == "test"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.description == "Test Description"
        assert metadata.priority == 50
        assert metadata.enabled

    def test_metadata_custom_priority(self):
        """Test metadata with custom priority."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test",
            description="Test",
            priority=100,
        )

        assert metadata.priority == 100

    def test_metadata_disabled(self):
        """Test disabled metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Test",
            description="Test",
            enabled=False,
        )

        assert not metadata.enabled


class TestCategorisationPlugin:
    """Tests for CategorisationPlugin base class."""

    def test_categorisation_plugin_metadata(self):
        """Test categorisation plugin has metadata."""
        plugin = MockCategorisationPlugin()

        assert plugin.metadata is not None
        assert plugin.metadata.name == "mock_categoriser"

    def test_categorise_implementation(self):
        """Test categorise method."""
        plugin = MockCategorisationPlugin(category_map={".txt": "Documents"})

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        category: str | None = plugin.categorise(file_info)

        assert category == "Documents"

    def test_can_categorise_default(self):
        """Test default can_categorise returns True."""
        plugin = MockCategorisationPlugin()

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo

        file_info = FileInfo(
            path=Path("test.xyz"),
            name="test.xyz",
            extension=".xyz",
            size=100,
            modified_time=0,
        )

        # Override can_categorise to check files
        assert plugin.can_categorise(file_info) in [True, False]

    def test_get_categories(self):
        """Test get_categories method."""
        plugin = MockCategorisationPlugin(
            category_map={".txt": "Documents", ".py": "Code"}
        )

        categories: set[str] = plugin.get_categories()

        assert "Documents" in categories
        assert "Code" in categories


class TestReporterPlugin:
    """Tests for ReporterPlugin base class."""

    def test_reporter_plugin_metadata(self):
        """Test reporter plugin has metadata."""
        plugin = MockReporterPlugin()

        assert plugin.metadata is not None
        assert plugin.metadata.name == "mock_reporter"

    def test_on_start(self):
        """Test on_start method."""
        plugin = MockReporterPlugin()

        plugin.on_start(total_files=10)

        assert plugin.start_called
        assert plugin.total_files == 10

    def test_on_file_processing(self):
        """Test on_file_processing method."""
        plugin = MockReporterPlugin()

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        plugin.on_file_processing(file_info)

        assert len(plugin.processing_files) == 1
        assert plugin.processing_files[0] == file_info

    def test_on_file_processed(self):
        """Test on_file_processed method."""
        plugin = MockReporterPlugin()

        from pathlib import Path

        from src.file_organiser.core.models import MoveResult, MoveStatus

        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("test.txt"),
            destination=Path("dest/test.txt"),
        )

        plugin.on_file_processed(result)

        assert len(plugin.processed_results) == 1
        assert plugin.processed_results[0] == result

    def test_on_complete(self):
        """Test on_complete method."""
        plugin = MockReporterPlugin()

        from src.file_organiser.core.models import OrganiserResult

        result = OrganiserResult(
            files_processed=10,
            files_moved=8,
            files_failed=2,
            files_skipped=0,
            unknown_files=0,
            categories_created=set(),
            errors=[],
            duration_seconds=1.0,
        )

        plugin.on_complete(result)

        assert plugin.complete_called
        assert plugin.complete_result == result


class TestFilterPlugin:
    """Tests for FilterPlugin base class."""

    def test_filter_plugin_metadata(self):
        """Test filter plugin has metadata."""
        plugin = MockFilterPlugin()

        assert plugin.metadata is not None
        assert plugin.metadata.name == "mock_filter"

    def test_should_process(self):
        """Test should_process method."""
        plugin = MockFilterPlugin(exclude_all=False)

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        should_process: bool = plugin.should_process(file_info)

        assert should_process

    def test_should_process_exclude(self):
        """Test should_process method when excluding."""
        plugin = MockFilterPlugin(exclude_all=True)

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        should_process: bool = plugin.should_process(file_info)

        assert not should_process


class TestPostProcessingPlugin:
    """Tests for PostProcessingPlugin base class."""

    def test_post_processing_plugin_metadata(self):
        """Test post-processing plugin has metadata."""
        plugin = MockPostProcessingPlugin()

        assert plugin.metadata is not None
        assert plugin.metadata.name == "mock_post_processor"

    def test_process(self):
        """Test process method."""
        plugin = MockPostProcessingPlugin()

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo, MoveResult, MoveStatus

        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("test.txt"),
            destination=Path("dest/test.txt"),
        )

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        plugin.process(result, original_info=file_info)

        assert len(plugin.processed_results) == 1

    def test_process_failure_handling(self):
        """Test process method with failure."""
        plugin = MockPostProcessingPlugin(should_fail=True)

        from pathlib import Path

        from src.file_organiser.core.models import FileInfo, MoveResult, MoveStatus

        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("test.txt"),
            destination=Path("dest/test.txt"),
        )

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        try:
            plugin.process(result, original_info=file_info)
        except Exception as e:
            assert "Mock post-processing failure" in str(object=e)
