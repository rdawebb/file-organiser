"""Plugin registry for managing file organiser plugins."""

from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from _frozen_importlib import ModuleSpec
    from types import ModuleType

from ..utils.logging import get_logger
from .base import (
    CategorisationPlugin,
    FilterPlugin,
    Plugin,
    PluginMetadata,
    PostProcessingPlugin,
    ReporterPlugin,
)

logger: Logger = get_logger(name=__name__)


class PluginRegistry:
    """Registry for managing plugins."""

    def __init__(self) -> None:
        """Initialises the plugin registry."""
        self._categorisation_plugins: List[CategorisationPlugin] = []
        self._reporter_plugins: List[ReporterPlugin] = []
        self._filter_plugins: List[FilterPlugin] = []
        self._post_processing_plugins: List[PostProcessingPlugin] = []
        self._all_plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Registers a plugin in the appropriate category.

        Args:
            plugin (Plugin): The plugin instance to register.
        """
        metadata: PluginMetadata = plugin.metadata

        if metadata.name in self._all_plugins:
            logger.warning(
                msg=f"Plugin '{metadata.name}' already registered - replacing."
            )

        if isinstance(plugin, CategorisationPlugin):
            self._categorisation_plugins.append(plugin)
            self._categorisation_plugins.sort(
                key=lambda p: p.metadata.priority, reverse=True
            )

        if isinstance(plugin, ReporterPlugin):
            self._reporter_plugins.append(plugin)

        if isinstance(plugin, FilterPlugin):
            self._filter_plugins.append(plugin)

        if isinstance(plugin, PostProcessingPlugin):
            self._post_processing_plugins.append(plugin)

        self._all_plugins[metadata.name] = plugin
        logger.info(msg=f"Registered plugin: {metadata.name} (v{metadata.version})")

    def unregister(self, plugin_name: str) -> None:
        """Unregisters a plugin by name.

        Args:
            plugin_name (str): The name of the plugin to unregister.
        """
        if plugin_name not in self._all_plugins:
            logger.warning(msg=f"Plugin '{plugin_name}' not found in registry.")
            return

        plugin: Plugin = self._all_plugins[plugin_name]

        self._categorisation_plugins: list[CategorisationPlugin] = [
            p for p in self._categorisation_plugins if p.metadata.name != plugin_name
        ]
        self._reporter_plugins: list[ReporterPlugin] = [
            p for p in self._reporter_plugins if p.metadata.name != plugin_name
        ]
        self._filter_plugins: list[FilterPlugin] = [
            p for p in self._filter_plugins if p.metadata.name != plugin_name
        ]
        self._post_processing_plugins: list[PostProcessingPlugin] = [
            p for p in self._post_processing_plugins if p.metadata.name != plugin_name
        ]

        plugin.cleanup()
        del self._all_plugins[plugin_name]
        logger.info(msg=f"Unregistered plugin: {plugin_name}")

    def get_categorisation_plugins(self) -> List[CategorisationPlugin]:
        """Returns the list of registered categorisation plugins.

        Returns:
            List[CategorisationPlugin]: List of categorisation plugins.
        """
        return [p for p in self._categorisation_plugins if p.metadata.enabled]

    def get_filter_plugins(self) -> List[FilterPlugin]:
        """Returns the list of registered filter plugins.

        Returns:
            List[FilterPlugin]: List of filter plugins.
        """
        return [p for p in self._filter_plugins if p.metadata.enabled]

    def get_postprocess_plugins(self) -> List[PostProcessingPlugin]:
        """Returns the list of registered post-processing plugins.

        Returns:
            List[PostProcessingPlugin]: List of post-processing plugins.
        """
        return [p for p in self._post_processing_plugins if p.metadata.enabled]

    def get_default_reporter(self) -> Optional[ReporterPlugin]:
        """Returns the default reporter plugin, if any.

        Returns:
            Optional[ReporterPlugin]: The default reporter plugin or None.
        """
        enabled: list[ReporterPlugin] = [
            p for p in self._reporter_plugins if p.metadata.enabled
        ]
        return enabled[0] if enabled else None

    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Retrieves a plugin by name.

        Args:
            plugin_name (str): The name of the plugin to retrieve.

        Returns:
            Optional[Plugin]: The plugin instance if found, else None.
        """
        return self._all_plugins.get(plugin_name)

    def get_all_categories(self) -> Set[str]:
        """Returns a set of all categories provided by categorisation plugins.

        Returns:
            Set[str]: Set of all category names.
        """
        categories: set[str] = set()
        for plugin in self.get_categorisation_plugins():
            get_cats: Any | None = getattr(plugin, "get_categories", None)
            if callable(get_cats):
                categories.update(get_cats())
        categories.add("Unknown")

        return categories

    def list_plugins(self) -> dict[str, dict[str, Any]]:
        """Lists all registered plugins by name.

        Returns:
            List[str]: List of plugin names.
        """
        return {
            name: {
                "version": plugin.metadata.version,
                "author": plugin.metadata.author,
                "description": plugin.metadata.description,
                "enabled": plugin.metadata.enabled,
                "priority": plugin.metadata.priority,
                "type": type(plugin).__name__,
            }
            for name, plugin in self._all_plugins.items()
        }

    @classmethod
    def create_default(cls) -> "PluginRegistry":
        """Creates a default plugin registry with no plugins registered.

        Returns:
            PluginRegistry: A new instance of PluginRegistry.
        """
        from .builtin.extension import (
            ExtensionCategorisationPlugin,
        )
        from .builtin.reporters import RichReporterPlugin

        registry: PluginRegistry = cls()
        registry.register(plugin=ExtensionCategorisationPlugin(custom_extensions=None))
        registry.register(plugin=RichReporterPlugin())
        return registry

    def load_from_directory(self, plugins_dir: Path) -> None:
        """Loads and registers plugins from the specified directory.

        Args:
            plugins_dir (Path): The directory to load plugins from.
        """
        if not plugins_dir.exists():
            logger.warning(msg=f"Plugins directory '{plugins_dir}' does not exist.")
            return

        for plugin_file in plugins_dir.glob(pattern="*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.error(msg=f"Failed to load plugin from '{plugin_file}': {e}")

    def _load_plugin_file(self, plugin_file: Path) -> None:
        """Loads a plugin from a single Python file.

        Args:
            plugin_file (Path): The path to the plugin file.
        """
        import importlib.util
        import sys

        spec: ModuleSpec | None = importlib.util.spec_from_file_location(
            name=plugin_file.stem, location=plugin_file
        )
        if not spec or not spec.loader:
            logger.error(msg=f"Could not load spec for plugin '{plugin_file}'.")
            return

        module: ModuleType = importlib.util.module_from_spec(spec)
        sys.modules[plugin_file.stem] = module
        spec.loader.exec_module(module)

        for name in dir(module):
            obj: Any = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                try:
                    plugin: Plugin = obj()
                    self.register(plugin)
                except Exception as e:
                    logger.error(msg=f"Error instantiating plugin '{name}': {e}")
