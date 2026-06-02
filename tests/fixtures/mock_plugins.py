"""Mock plugin implementations for testing."""

from typing import Optional

from file_organiser.core.models import FileInfo, MoveResult, OrganiserResult
from file_organiser.plugins.base import (
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
        self.name: str = name
        self.category_map: dict[str, str] = category_map or {
            ".txt": "Documents",
            ".py": "Code",
        }
        self.should_fail: bool = should_fail
        self.priority: int = priority
        self.call_count: int = 0
        self.categorised_files: list[FileInfo] = []
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
        """Get the plugin metadata.

        Returns:
            PluginMetadata instance
        """
        return self._metadata

    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorise a file.

        Args:
            file_info: FileInfo instance to categorise

        Returns:
            Category string if categorisation successful, None otherwise
        """
        self.call_count += 1
        self.categorised_files.append(file_info)

        if self.should_fail:
            raise Exception("Mock categorisation failure")

        return self.category_map.get(file_info.extension)

    def can_categorise(self, file_info: FileInfo) -> bool:
        """Check if plugin can categorise file.

        Args:
            file_info: FileInfo instance to check

        Returns:
            True if file can be categorised, False otherwise
        """
        return file_info.extension in self.category_map

    def get_categories(self) -> set[str]:
        """Get all categories this plugin provides.

        Returns:
            Set of all categories
        """
        return set(self.category_map.values())


class MockFilterPlugin(FilterPlugin):
    """Mock filter plugin for testing."""

    def __init__(self, name: str = "mock_filter", exclude_all: bool = False):
        """Initialize mock filter plugin.

        Args:
            name: Plugin name
            exclude_all: If True, exclude all files
        """
        self.name: str = name
        self.exclude_all: bool = exclude_all
        self.checked_files: list[FileInfo] = []
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock filter plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        """Get the plugin metadata.

        Returns:
            PluginMetadata instance
        """
        return self._metadata

    def should_process(self, file_info: FileInfo) -> bool:
        """Determine if file should be processed.

        Args:
            file_info: FileInfo instance to check

        Returns:
            True if file should be processed, False otherwise
        """
        self.checked_files.append(file_info)
        return not self.exclude_all


class MockReporterPlugin(ReporterPlugin):
    """Mock reporter plugin for testing."""

    def __init__(self, name: str = "mock_reporter"):
        """Initialize mock reporter plugin.

        Args:
            name: Plugin name
        """
        self.name: str = name
        self.start_called: bool = False
        self.total_files: int = 0
        self.processing_files: list[FileInfo] = []
        self.processed_results: list[MoveResult] = []
        self.complete_result: OrganiserResult
        self.complete_called: bool = False
        self._metadata: PluginMetadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock reporter plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        """Get the plugin metadata.

        Returns:
            PluginMetadata instance
        """
        return self._metadata

    def on_start(self, total_files: int) -> None:
        """Called when organisation starts.

        Args:
            total_files: Total number of files to process
        """
        self.start_called = True
        self.total_files: int = total_files

    def on_file_processing(self, file_info: FileInfo) -> None:
        """Called when processing a file.

        Args:
            file_info: FileInfo instance of file to process
        """
        self.processing_files.append(file_info)

    def on_file_processed(self, result: MoveResult) -> None:
        """Called when file is processed.

        Args:
            result: MoveResult instance of processed file
        """
        self.processed_results.append(result)

    def on_complete(self, result: OrganiserResult) -> None:
        """Called when organisation is complete.

        Args:
            result: OrganiserResult instance of completed organisation
        """
        self.complete_called = True
        self.complete_result: OrganiserResult = result


class MockPostProcessingPlugin(PostProcessingPlugin):
    """Mock post-processing plugin for testing."""

    def __init__(self, name: str = "mock_post_processor", should_fail: bool = False):
        """Initialize mock post-processing plugin.

        Args:
            name: Plugin name
            should_fail: If True, raise exception during post-processing
        """
        self.name: str = name
        self.should_fail: bool = should_fail
        self.processed_results: list[tuple[MoveResult, FileInfo]] = []
        self._metadata = PluginMetadata(
            name=self.name,
            version="0.1.0",
            author="Test",
            description="Mock post-processing plugin",
            enabled=True,
        )

    @property
    def metadata(self) -> PluginMetadata:
        """Get the plugin metadata.

        Returns:
            PluginMetadata instance
        """
        return self._metadata

    def process(self, result: MoveResult, original_info: FileInfo) -> None:
        """Post-process the organisation result.

        Args:
            result: MoveResult instance of processed file
            original_info: FileInfo instance of original file
        """
        self.processed_results.append((result, original_info))

        if self.should_fail:
            raise Exception("Mock post-processing failure")
