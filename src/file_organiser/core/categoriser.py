"""File categorisation logic using plugins."""

from logging import Logger
from pathlib import Path
from typing import Any, List, Optional

from ..plugins.base import CategorisationPlugin
from ..plugins.registry import PluginRegistry
from ..utils.logging import get_logger
from .models import FileInfo

logger: Logger = get_logger(name=__name__)


class FileCategoriser:
    """Categorises files using registered plugins."""

    def __init__(
        self,
        plugin_registry: Optional[PluginRegistry] = None,
        fallback_category: str = "Uncategorised",
    ) -> None:
        """Initialises the FileCategoriser with a plugin registry.

        Args:
            plugin_registry: The registry of categorisation plugins (defaults to None)
            fallback_category: The category to assign if no plugins match (defaults to "Uncategorised").
        """
        self.plugin_registry: PluginRegistry = (
            plugin_registry or PluginRegistry.create_default()
        )
        self.fallback_category: str = fallback_category
        self._plugin_cache: List[CategorisationPlugin] = []
        self._cache_valid: bool = False

    def categorise(self, file_info: FileInfo) -> str:
        """Categorises a file based on the registered plugins.

        Args:
            file_info (FileInfo): The file information to categorise.

        Returns:
            str: The determined category for the file.
        """
        plugins: list[CategorisationPlugin] = self._get_plugins()

        for plugin in plugins:
            try:
                if hasattr(plugin, "can_categorise"):
                    if not plugin.can_categorise(file_info):
                        continue

                category: str | None = plugin.categorise(file_info)

                if category:
                    logger.debug(
                        msg=f"File '{file_info.name}' categorised as '{category}' by plugin '{plugin.metadata.name}'"
                    )
                    return category

            except Exception as e:
                logger.error(
                    msg=f"Plugin '{plugin.metadata.name}' failed to categorise file '{file_info.name}': {e}"
                )
                continue

        logger.debug(
            msg=f"File '{file_info.name}' could not be categorised by any plugin, using fallback category '{self.fallback_category}'"
        )
        return self.fallback_category

    def categorise_batch(self, file_infos: List[FileInfo]) -> dict[Path, str]:
        """Categorises a batch of files.

        Args:
            file_infos (List[FileInfo]): List of file information objects to categorise.

        Returns:
            dict[Path, str]: Dictionary mapping file paths to their determined categories.
        """
        results: dict[Path, str] = {}
        for file_info in file_infos:
            category: str = self.categorise(file_info)
            results[file_info.path] = category
        return results

    def get_all_categories(self) -> set[str]:
        """Retrieves all possible categories from the registered plugins.

        Returns:
            set[str]: Set of all category names.
        """
        categories: set[str] = {self.fallback_category}

        for plugin in self._get_plugins():
            if hasattr(plugin, "get_categories"):
                try:
                    get_cats: Any | None = getattr(plugin, "get_categories", None)
                    if callable(get_cats):
                        categories.update(get_cats())
                except Exception as e:
                    logger.error(
                        msg=f"Plugin '{plugin.metadata.name}' failed to get categories: {e}"
                    )
                    continue

        return categories

    def get_category_info(self, category: str) -> dict:
        """Retrieves information about a specific category.

        Args:
            category (str): The category name to retrieve information for.

        Returns:
            dict: Information about the category, including which plugins provide it.
        """
        info: dict[str, str | list | None] = {
            "name": category,
            "provided_by": [],
            "description": None,
        }

        for plugin in self._get_plugins():
            try:
                get_cats: Any | None = getattr(plugin, "get_categories", None)
                if callable(get_cats):
                    provided_by: list[str] = info["provided_by"]
                    if not isinstance(provided_by, list) or provided_by is None:
                        provided_by: list[str] = []
                    provided_by.append(plugin.metadata.name)
            except Exception:
                pass

        return info

    def _get_plugins(self) -> List[CategorisationPlugin]:
        """Retrieves and caches the list of categorisation plugins.

        Returns:
            List[CategorisationPlugin]: List of categorisation plugins.
        """
        if not self._cache_valid:
            self._plugin_cache: list[CategorisationPlugin] = (
                self.plugin_registry.get_categorisation_plugins()
            )
            self._cache_valid = True

        return self._plugin_cache

    def _invalidate_cache(self) -> None:
        """Invalidates the plugin cache."""
        self._cache_valid = False
        logger.debug(msg="Categorisation plugin cache invalidated.")

    def get_statistics(self) -> dict:
        """Retrieves statistics about the categorisation plugins.

        Returns:
            dict: Statistics including number of plugins and categories.
        """
        plugins: list[CategorisationPlugin] = self._get_plugins()

        return {
            "total_plugins": len(plugins),
            "enabled_plugins": len(
                [p for p in plugins if getattr(p.metadata, "enabled", True)]
            ),
            "total_categories": len(self.get_all_categories()),
            "fallback_category": self.fallback_category,
            "plugins": [
                {
                    "name": p.metadata.name,
                    "priority": p.metadata.priority,
                    "enabled": p.metadata.enabled,
                }
                for p in plugins
            ],
        }


class CategoryResolver:
    """Resolves file categories using plugins and file information."""

    def __init__(self) -> None:
        """Initialises the CategoryResolver"""
        self._category_metadata: dict[str, dict] = {}

    def register_category(
        self,
        name: str,
        display_name: str | None,
        description: str | None,
        icon: str | None,
    ) -> None:
        """Registers metadata for a category.

        Args:
            name (str): The category name.
            display_name (str, optional): Human-readable name for the category.
            description (str, optional): A description of the category.
            icon (str, optional): An icon representing the category.
        """
        self._category_metadata[name] = {
            "name": name,
            "display_name": display_name or name.replace("_", " ").title(),
            "description": description or f"Files in the {name} category",
            "icon": icon or "📁",
        }

    def get_display_name(self, category: str) -> str:
        """Get human-readable display name for a category."""
        if category in self._category_metadata:
            return self._category_metadata[category]["display_name"]
        return category.replace("_", " ").title()

    def get_icon(self, category: str) -> str:
        """Get icon for a category."""
        if category in self._category_metadata:
            return self._category_metadata[category]["icon"]
        return "📁"

    def get_metadata(self, category: str) -> dict:
        """Get full metadata for a category."""
        return self._category_metadata.get(
            category,
            {
                "name": category,
                "display_name": category.replace("_", " ").title(),
                "description": f"Files in the {category} category",
                "icon": "📁",
            },
        )


_resolver = CategoryResolver()


def register_category_metadata(
    name: str, display_name: str | None, description: str | None, icon: str | None
) -> None:
    """Registers category metadata globally.

    Args:
        name (str): The category name.
        display_name (str, optional): Human-readable name for the category.
        description (str, optional): A description of the category.
        icon (str, optional): An icon representing the category.
    """
    _resolver.register_category(name, display_name, description, icon)


def get_category_display_name(category: str) -> str:
    """Get human-readable display name for a category."""
    return _resolver.get_display_name(category)


def get_category_icon(category: str) -> str:
    """Get icon for a category."""
    return _resolver.get_icon(category)


def get_category_metadata(category: str) -> dict:
    """Get full metadata for a category."""
    return _resolver.get_metadata(category)


# Register category metadata

register_category_metadata(
    name="archives",
    display_name="Archives",
    description="Compressed archive files",
    icon="📦",
)
register_category_metadata(
    name="audio", display_name="Audio", description="Audio files", icon="🎵"
)
register_category_metadata(
    name="code", display_name="Code", description="Source code files", icon="💻"
)
register_category_metadata(
    name="data_files",
    display_name="Data Files",
    description="Data files such as CSV, JSON, XML",
    icon="📊",
)
register_category_metadata(
    name="design_files",
    display_name="Design Files",
    description="Design and graphics files",
    icon="🎨",
)
register_category_metadata(
    name="disks_images",
    display_name="Disk Images",
    description="Disk image files",
    icon="💿",
)
register_category_metadata(
    name="documents", display_name="Documents", description="Document files", icon="📄"
)
register_category_metadata(
    name="ebooks", display_name="eBooks", description="Electronic book files", icon="📚"
)
register_category_metadata(
    name="fonts", display_name="Fonts", description="Font files", icon="🔤"
)
register_category_metadata(
    name="images", display_name="Images", description="Image files", icon="🖼️"
)
register_category_metadata(
    name="installers",
    display_name="Installers",
    description="Software installer files",
    icon="🛠️",
)
register_category_metadata(
    name="misc",
    display_name="Miscellaneous",
    description="Miscellaneous files",
    icon="🗂️",
)
register_category_metadata(
    name="raw_images",
    display_name="Raw Images",
    description="Raw image files from cameras",
    icon="📷",
)
register_category_metadata(
    name="text", display_name="Text Files", description="Plain text files", icon="📝"
)
register_category_metadata(
    name="videos", display_name="Videos", description="Video files", icon="🎬"
)
register_category_metadata(
    name="web", display_name="Web Files", description="Web-related files", icon="🌐"
)
register_category_metadata(
    name="3d_files",
    display_name="3D Files",
    description="3D model and design files",
    icon="🧱",
)
register_category_metadata(
    name="Uncategorised",
    display_name="Uncategorised",
    description="Files that could not be categorised",
    icon="❓",
)
