"""Plugin for categorising files based on their extensions."""

from typing import Optional, Set

from ...core.models import FileInfo
from ...data.default_extensions import DEFAULT_EXTENSIONS
from ..base import CategorisationPlugin, PluginMetadata


class ExtensionCategorisationPlugin(CategorisationPlugin):
    """Categorisation plugin based on file extensions."""

    def __init__(self, custom_extensions: Optional[dict[str, str]]) -> None:
        """Initialises the ExtensionCategorisationPlugin.

        Args:
            custom_extensions (Optional[dict[str, str]]): A dictionary mapping file extensions
                to category names. If None, uses the default EXTENSIONS mapping.
        """
        self._extensions: dict[str, str] = DEFAULT_EXTENSIONS
        if custom_extensions:
            self._extensions.update(custom_extensions)

        self._multi_part: list[str] = [".tar.gz", ".tar.bz2", ".tar.xz"]

    @property
    def metadata(self) -> PluginMetadata:
        """Returns the metadata for the plugin.

        Returns:
            PluginMetadata: The metadata for the plugin.
        """
        return PluginMetadata(
            name="extension_categoriser",
            version="0.1.0",
            author="Rob Webb",
            description="Categorises files by file extension",
            priority=10,  # high priority
        )

    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorises a file based on its extension.

        Args:
            file_info (FileInfo): Information about the file to categorise.

        Returns:
            Optional[str]: The category name if categorised, else None.
        """
        filename_lower: str = file_info.name.lower()

        for ext in self._multi_part:
            if filename_lower.endswith(ext):
                return self._extensions.get(ext)

        return self._extensions.get(file_info.extension)

    def can_categorise(self, file_info: FileInfo) -> bool:
        """Quick check to see if the plugin can categorise the file.

        Args:
            file_info (FileInfo): Information about the file to check.

        Returns:
            bool: True if the plugin can categorise the file, else False.
        """
        name_lower = file_info.name.lower()
        if any(name_lower.endswith(ext) for ext in self._multi_part):
            return True
        return file_info.extension in self._extensions

    def get_categories(self) -> Set[str]:
        """Returns the set of categories this plugin can categorise into.

        Returns:
            Set[str]: A set of category names.
        """
        return set(self._extensions.values())
