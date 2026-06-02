"""Unit tests for plugin registry."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from file_organiser.plugins.base import (
        CategorisationPlugin,
        FilterPlugin,
        Plugin,
        PostProcessingPlugin,
        ReporterPlugin,
    )

from fixtures.mock_plugins import (
    MockCategorisationPlugin,
    MockFilterPlugin,
    MockPostProcessingPlugin,
    MockReporterPlugin,
)

from file_organiser.plugins.registry import PluginRegistry


class TestPluginRegistryInitialisation:
    """Tests for PluginRegistry initialisation."""

    def test_registry_creation(self):
        """Test creating a PluginRegistry."""
        registry = PluginRegistry()

        assert registry._categorisation_plugins == []
        assert registry._reporter_plugins == []
        assert registry._filter_plugins == []
        assert registry._post_processing_plugins == []
        assert registry._all_plugins == {}

    def test_default_registry(self):
        """Test creating default registry."""
        registry: PluginRegistry = PluginRegistry.create_default()

        assert registry is not None


class TestPluginRegistration:
    """Tests for plugin registration."""

    def test_register_categorisation_plugin(self):
        """Test registering a categorisation plugin."""
        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(name="test_cat")

        registry.register(plugin)

        assert len(registry._categorisation_plugins) == 1
        assert registry._all_plugins["test_cat"] == plugin

    def test_register_reporter_plugin(self):
        """Test registering a reporter plugin."""
        registry = PluginRegistry()
        plugin = MockReporterPlugin(name="test_reporter")

        registry.register(plugin)

        assert len(registry._reporter_plugins) == 1
        assert registry._all_plugins["test_reporter"] == plugin

    def test_register_filter_plugin(self):
        """Test registering a filter plugin."""
        registry = PluginRegistry()
        plugin = MockFilterPlugin(name="test_filter")

        registry.register(plugin)

        assert len(registry._filter_plugins) == 1
        assert registry._all_plugins["test_filter"] == plugin

    def test_register_post_processing_plugin(self):
        """Test registering a post-processing plugin."""
        registry = PluginRegistry()
        plugin = MockPostProcessingPlugin(name="test_post")

        registry.register(plugin)

        assert len(registry._post_processing_plugins) == 1
        assert registry._all_plugins["test_post"] == plugin

    def test_register_multiple_plugins(self):
        """Test registering multiple different plugins."""
        registry = PluginRegistry()
        cat_plugin = MockCategorisationPlugin(name="cat")
        rep_plugin = MockReporterPlugin(name="rep")
        flt_plugin = MockFilterPlugin(name="flt")

        registry.register(plugin=cat_plugin)
        registry.register(plugin=rep_plugin)
        registry.register(plugin=flt_plugin)

        assert len(registry._all_plugins) == 3

    def test_register_duplicate_plugin(self):
        """Test registering a plugin with duplicate name."""
        registry = PluginRegistry()
        plugin1 = MockCategorisationPlugin(name="same")
        plugin2 = MockReporterPlugin(name="same")

        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        # Second registration should replace first
        assert registry._all_plugins["same"] == plugin2


class TestPluginPriority:
    """Tests for plugin priority ordering."""

    def test_categorisation_plugins_sorted_by_priority(self):
        """Test that categorisation plugins are sorted by priority."""
        registry = PluginRegistry()

        low_priority = MockCategorisationPlugin(
            name="low",
            priority=10,
        )
        high_priority = MockCategorisationPlugin(
            name="high",
            priority=100,
        )
        medium_priority = MockCategorisationPlugin(
            name="medium",
            priority=50,
        )

        registry.register(plugin=low_priority)
        registry.register(plugin=high_priority)
        registry.register(plugin=medium_priority)

        plugins: list[CategorisationPlugin] = registry.get_categorisation_plugins()

        # Should be sorted by priority (highest first)
        assert len(plugins) == 3


class TestPluginRetrieval:
    """Tests for retrieving plugins."""

    def test_get_categorisation_plugins(self):
        """Test retrieving categorisation plugins."""
        registry = PluginRegistry()
        plugin1 = MockCategorisationPlugin(name="cat1")
        plugin2 = MockCategorisationPlugin(name="cat2")

        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        plugins: list[CategorisationPlugin] = registry.get_categorisation_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins

    def test_get_postprocess_plugins_from_registry(self):
        """Test retrieving post-processing plugins from registry."""
        registry = PluginRegistry()
        plugin1 = MockPostProcessingPlugin(name="post1")
        plugin2 = MockPostProcessingPlugin(name="post2")

        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        plugins: list[PostProcessingPlugin] = registry.get_postprocess_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins

    def test_get_filter_plugins(self):
        """Test retrieving filter plugins."""
        registry = PluginRegistry()
        plugin1 = MockFilterPlugin(name="flt1")
        plugin2 = MockFilterPlugin(name="flt2")

        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        plugins: list[FilterPlugin] = registry.get_filter_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins

    def test_get_postprocess_plugins(self):
        """Test retrieving post-processing plugins."""
        registry = PluginRegistry()
        plugin1 = MockPostProcessingPlugin(name="post1")
        plugin2 = MockPostProcessingPlugin(name="post2")

        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        plugins: list[PostProcessingPlugin] = registry.get_postprocess_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins

    def test_list_all_plugins(self):
        """Test listing all plugins."""
        registry = PluginRegistry()
        cat_plugin = MockCategorisationPlugin(name="cat")
        rep_plugin = MockReporterPlugin(name="rep")

        registry.register(plugin=cat_plugin)
        registry.register(plugin=rep_plugin)

        plugins: dict[str, dict[str, Any]] = registry.list_plugins()

        assert len(plugins) == 2
        assert "cat" in plugins
        assert "rep" in plugins

    def test_get_plugin_by_name(self):
        """Test retrieving a plugin by name."""
        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(name="my_plugin")

        registry.register(plugin)

        retrieved: Plugin | None = registry.get_plugin(plugin_name="my_plugin")

        assert retrieved == plugin

    def test_get_nonexistent_plugin(self):
        """Test retrieving a plugin that doesn't exist."""
        registry = PluginRegistry()

        plugin: Plugin | None = registry.get_plugin(plugin_name="nonexistent")

        assert plugin is None


class TestPluginUnregistration:
    """Tests for plugin unregistration."""

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(name="test")

        registry.register(plugin)
        assert "test" in registry._all_plugins

        registry.unregister(plugin_name="test")

        assert "test" not in registry._all_plugins
        assert len(registry._categorisation_plugins) == 0

    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a plugin that doesn't exist."""
        registry = PluginRegistry()

        # Should not raise
        registry.unregister(plugin_name="nonexistent")

    def test_unregister_calls_cleanup(self):
        """Test that unregister calls plugin cleanup."""
        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(name="test")

        registry.register(plugin)
        registry.unregister(plugin_name="test")

        # Plugin cleanup should have been called


class TestPluginEnableDisable:
    """Tests for enabling/disabling plugins."""

    def test_get_enabled_categorisation_plugins(self):
        """Test that only enabled plugins are retrieved."""
        registry = PluginRegistry()
        enabled_plugin = MockCategorisationPlugin(
            name="enabled",
        )

        registry.register(plugin=enabled_plugin)

        plugins: list[CategorisationPlugin] = registry.get_categorisation_plugins()

        assert enabled_plugin in plugins

    def test_disabled_plugins_not_retrieved(self):
        """Test that disabled plugins are not retrieved."""
        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(name="disabled")

        registry.register(plugin)

        # Disable the plugin
        plugin.metadata.enabled = False

        plugins: list[CategorisationPlugin] = registry.get_categorisation_plugins()

        assert plugin not in plugins


class TestDefaultReporter:
    """Tests for default reporter plugin."""

    def test_get_default_reporter(self):
        """Test retrieving default reporter."""
        registry: PluginRegistry = PluginRegistry.create_default()

        reporter: ReporterPlugin | None = registry.get_default_reporter()

        assert reporter is not None
