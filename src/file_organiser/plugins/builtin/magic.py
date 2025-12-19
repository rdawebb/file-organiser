"""Magic number based categorisation plugin."""

from typing import Optional, Set

from src.file_organiser.core.models import FileInfo
from ..base import CategoriserPlugin, PluginMetadata


class MagicNumberCategorisationPlugin(CategoriserPlugin):
    """Categorisation plugin based on file magic numbers."""

    def __init__(self) -> None:
        """Initialises the magic number categorisation plugin."""
        self._signatures = {
            b"\x89PNG\r\n\x1a\n": "images",
            b"\xff\xd8\xff": "images",  # JPEG
            b"GIF87a": "images",
            b"GIF89a": "images",
            b"%PDF": "documents",
            b"PK\x03\x04": "archives",  # ZIP
            b"PK\x05\x06": "archives",  # ZIP empty
            b"PK\x07\x08": "archives",  # ZIP spanned
            b"\x1f\x8b": "archives",  # GZIP
            b"Rar!\x1a\x07": "archives",  # RAR
            b"7z\xbc\xaf\x27\x1c": "archives",  # 7-Zip
            b"BM": "images",  # BMP
            b"II*\x00": "images",  # TIFF (little endian)
            b"MM\x00*": "images",  # TIFF (big endian)
        }

    @property
    def metadata(self) -> PluginMetadata:
        """Returns the metadata for the plugin.

        Returns:
            PluginMetadata: The metadata for the plugin.
        """
        return PluginMetadata(
            name="magic_categoriser",
            version="0.1.0",
            author="Rob Webb",
            description="Categorises files by magic numbers (file headers)",
            priority=20,
        )

    def categorise(self, file_info: FileInfo) -> Optional[str]:
        """Categorises a file based on its magic number.

        Args:
            file_info (FileInfo): Information about the file to categorise.

        Returns:
            Optional[str]: The category name if categorised, else None.
        """
        try:
            with open(file_info.path, "rb") as f:
                file_header = f.read(16)

            for signature, category in self._signatures.items():
                if file_header.startswith(signature):
                    return category

        except (OSError, PermissionError):
            pass

        return None

    def get_categories(self) -> Set[str]:
        """Returns the set of categories provided by this plugin.

        Returns:
            Set[str]: Set of category names.
        """
        return set(self._signatures.values())
