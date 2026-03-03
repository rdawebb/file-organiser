"""Mock plugin implementations for testing."""

from typing import Optional

from src.file_organiser.core.models import FileInfo, MoveResult, OrganiserResult
from src.file_organiser.plugins.base import (
    CategorisationPlugin,
    FilterPlugin,
    PluginMetadata,
    PostProcessingPlugin,
    ReporterPlugin,
)


class MockCategorisationPlugin(CategorisationPlugin):
    """Mock categorisation plugin for testing."""

    def __init__(
        self,
        name: str = "mock_categoriser",
        category_map: Optional[dict] = None,
        should_fail: bool = False,
        priority: int = 50,
    ):
        """Initialise mock plugin.

        Args:
            name: Plugin name
            category_map: Dict mapping extensions to categories
            should_fail: If True, raise exception during categorisation
            priority: Plugin priority
        """
        self.name = name
        self.category_map = category_map or {".txt": "Documents", ".py": "Code"}
        self.should_fail = should_fail
        self.priority = priority
        self.call_count = 0
        self.categorised_files = []
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock categorisation plugin",
            priority=self.priority,
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorise a file."""
        self.call_count += 1
        self.categorised_files.append(file_info)

        if self.should_fail:
            raise Exception("Mock categorisation failure")

        return self.category_map.get(file_info.extension)

    def can_categorise(self, file_info: FileInfo) -> bool:
        """Check if plugin can categorise file."""
        return file_info.extension in self.category_map

    def get_categories(self) -> set[str]:
        """Get all categories this plugin provides."""
        return set(self.category_map.values())


class MockFilterPlugin(FilterPlugin):
    """Mock filter plugin for testing."""

    def __init__(self, name: str = "mock_filter", exclude_all: bool = False):
        """Initialize mock filter plugin.

        Args:
            name: Plugin name
            exclude_all: If True, exclude all files
        """
        self.name = name
        self.exclude_all = exclude_all
        self.checked_files = []
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock filter plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def should_process(self, file_info: FileInfo) -> bool:
        """Determine if file should be processed."""
        self.checked_files.append(file_info)
        return not self.exclude_all


class MockReporterPlugin(ReporterPlugin):
    """Mock reporter plugin for testing."""

    def __init__(self, name: str = "mock_reporter"):
        """Initialize mock reporter plugin.

        Args:
            name: Plugin name
        """
        self.name = name
        self.start_called = False
        self.total_files = 0
        self.processing_files = []
        self.processed_results = []
        self.complete_result = None
        self.complete_called = False
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock reporter plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def on_start(self, total_files: int) -> None:
        """Called when organisation starts."""
        self.start_called = True
        self.total_files = total_files

    def on_file_processing(self, file_info: FileInfo) -> None:
        """Called when processing a file."""
        self.processing_files.append(file_info)

    def on_file_processed(self, result: MoveResult) -> None:
        """Called when file is processed."""
        self.processed_results.append(result)

    def on_complete(self, result: OrganiserResult) -> None:
        """Called when organisation is complete."""
        self.complete_called = True
        self.complete_result = result


class MockPostProcessingPlugin(PostProcessingPlugin):
    """Mock post-processing plugin for testing."""

    def __init__(self, name: str = "mock_post_processor", should_fail: bool = False):
        """Initialize mock post-processing plugin.

        Args:
            name: Plugin name
            should_fail: If True, raise exception during post-processing
        """
        self.name = name
        self.should_fail = should_fail
        self.processed_results = []
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock post-processing plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def process(self, result: MoveResult, original_info: FileInfo) -> None:
        """Post-process the organisation result."""
        self.processed_results.append((result, original_info))

        if self.should_fail:
            raise Exception("Mock post-processing failure")
