"""Plugin for categorising files based on their extensions."""

import json
from pathlib import Path
from typing import Optional, Set

from file_organiser.core.models import FileInfo
from ..base import CategoriserPlugin, PluginMetadata

EXTENSIONS_PATH = (
    Path(__file__).parent.parent.parent / "data" / "default_extensions.json"
)
with open(EXTENSIONS_PATH, "r", encoding="utf-8") as f:
    EXTENSIONS = json.load(f)


class ExtensionCategorisationPlugin(CategoriserPlugin):
    """Categorisation plugin based on file extensions."""

    def __init__(self, custom_extensions: Optional[dict[str, str]]) -> None:
        """Initialises the ExtensionCategorisationPlugin.

        Args:
            custom_extensions (Optional[dict[str, str]]): A dictionary mapping file extensions
                to category names. If None, uses the default EXTENSIONS mapping.
        """
        self._extensions = EXTENSIONS.copy()
        if custom_extensions:
            self._extensions.update(custom_extensions)

        self._multi_part = [".tar.gz", ".tar.bz2", ".tar.xz"]

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
        filename_lower = file_info.name.lower()

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
        return file_info.extension in self._extensions

    def get_categories(self) -> Set[str]:
        """Returns the set of categories this plugin can categorise into.

        Returns:
            Set[str]: A set of category names.
        """
        return set(self._extensions.values())
