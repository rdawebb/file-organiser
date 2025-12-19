"""MIME type based categorisation plugin."""

import mimetypes
from typing import Optional, Set

from src.file_organiser.core.models import FileInfo
from ..base import CategoriserPlugin, PluginMetadata


class MimeTypeCategorisationPlugin(CategoriserPlugin):
    """Categorisation plugin based on MIME types."""

    def __init__(self) -> None:
        """Initialises the MIME type categorisation plugin."""
        self._mime_mapping = {
            "text": "text",
            "image": "images",
            "audio": "audio",
            "video": "videos",
            "application": "documents",
            "font": "fonts",
        }

    @property
    def metadata(self) -> PluginMetadata:
        """Returns the metadata for the plugin.

        Returns:
            PluginMetadata: The metadata for the plugin.
        """
        return PluginMetadata(
            name="mime_categoriser",
            version="0.1.0",
            author="Rob Webb",
            description="Categorises files by MIME type",
            priority=30,
        )

    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorises a file based on its MIME type.

        Args:
            file_info (FileInfo): Information about the file to categorise.

        Returns:
            Optional[str]: The category name if categorised, else None.
        """
        mime_type, _ = mimetypes.guess_type(str(file_info.path))
        if not mime_type:
            return None

        main_type = mime_type.split("/")[0]

        return self._mime_mapping.get(main_type)

    def get_categories(self) -> Set[str]:
        """Returns the set of categories provided by this plugin.

        Returns:
            Set[str]: Set of category names.
        """
        return set(self._mime_mapping.values())
