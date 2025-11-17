"""Base classes and structures for plugins in the file organiser system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from file_organiser.core.models import FileInfo, MoveResult, OrganiserResult


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    author: str
    description: str
    priority: int = 50
    enabled: bool = True


class Plugin(ABC):
    """Abstract base class for all plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Returns the metadata for the plugin."""
        ...

    def initialise(self, config: Dict[str, Any]) -> None:
        """Initialises the plugin with the given configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary for the plugin.
        """
        pass

    def cleanup(self) -> None:
        """Cleans up any resources used by the plugin."""
        pass


class CategorisationPlugin(Plugin):
    """Abstract base class for categorisation plugins."""

    @abstractmethod
    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorises a file based on its FileInfo.

        Args:
            file_info (FileInfo): Information about the file to categorise.

        Returns:
            Optional[str]: The category name if categorised, else None.
        """
        ...

    def can_categorise(self, file_info: FileInfo) -> bool:
        """Quick check to see if the plugin can categorise the file.

        Args:
            file_info (FileInfo): Information about the file to check.

        Returns:
            bool: True if the plugin can categorise the file, else False.
        """
        return True


class ReporterPlugin(Plugin):
    """Abstract base class for progressing reporting plugins."""

    def on_start(self, total_files: int) -> None:
        """Called when the organisation process starts.

        Args:
            total_files (int): The total number of files to be processed.
        """
        pass

    def on_file_processing(self, file_info: FileInfo) -> None:
        """Called when a file is about to be processed.

        Args:
            file_info (FileInfo): Information about the file being processed.
        """
        pass

    def on_file_processed(self, result: MoveResult) -> None:
        """Called when a file has been processed.

        Args:
            result (MoveResult): The result of the file move operation.
        """
        pass

    def on_complete(self, result: OrganiserResult) -> None:
        """Called when the organisation process is complete.

        Args:
            organiser_result (OrganiserResult): The overall result of the organisation process.
        """
        pass

    def on_error(self, error: Exception, file_info: Optional[FileInfo] = None) -> None:
        """Called when an error occurs during file processing.

        Args:
            file_info (FileInfo): Information about the file being processed.
            error (Exception): The exception that occurred.
        """
        pass


class FilterPlugin(Plugin):
    """Abstract base class for file filter plugins."""

    @abstractmethod
    def should_process(self, file_info: FileInfo) -> bool:
        """Determines whether a file should be processed.

        Args:
            file_info (FileInfo): Information about the file to check.

        Returns:
            bool: True if the file should be processed, else False.
        """
        ...


class PostProcessingPlugin(Plugin):
    """Abstract base class for post-processing plugins."""

    @abstractmethod
    def process(self, result: MoveResult, original_info: FileInfo) -> None:
        """Processes the result of a file move operation.

        Examples:
            Update a database, log information, send notifications, etc.

        Args:
            result (MoveResult): The result of the file move operation.
            original_info (FileInfo): The original information about the file.
        """
        ...
