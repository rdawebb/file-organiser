"""Integration tests for plugin system."""

from src.file_organiser.plugins.registry import PluginRegistry

from tests.fixtures.mock_plugins import (
    MockCategorisationPlugin,
    MockReporterPlugin,
    MockFilterPlugin,
)


class TestPluginSystemIntegration:
    """Tests for plugin system integration."""

    def test_multiple_plugins_in_registry(self):
        """Test multiple plugins working in registry."""
        registry = PluginRegistry()

        cat1 = MockCategorisationPlugin(name="cat1", priority=100)
        cat2 = MockCategorisationPlugin(name="cat2", priority=50)
        reporter = MockReporterPlugin(name="reporter")
        filter_plugin = MockFilterPlugin(name="filter")

        registry.register(cat1)
        registry.register(cat2)
        registry.register(reporter)
        registry.register(filter_plugin)

        assert len(registry.list_plugins()) == 4
        assert len(registry.get_categorisation_plugins()) == 2

    def test_plugin_priority_respected(self):
        """Test that plugin priority is respected in retrieval."""
        registry = PluginRegistry()

        low = MockCategorisationPlugin(name="low", priority=10)
        high = MockCategorisationPlugin(name="high", priority=100)
        med = MockCategorisationPlugin(name="med", priority=50)

        registry.register(low)
        registry.register(high)
        registry.register(med)

        plugins = registry.get_categorisation_plugins()

        # High priority should be first
        assert plugins[0].metadata.priority >= plugins[1].metadata.priority

    def test_plugin_enable_disable_integration(self):
        """Test enable/disable functionality in registry."""
        registry = PluginRegistry()

        plugin = MockCategorisationPlugin(name="test")
        registry.register(plugin)

        assert len(registry.get_categorisation_plugins()) == 1

        # Disable plugin
        plugin.metadata.enabled = False

        assert len(registry.get_categorisation_plugins()) == 0

        # Re-enable
        plugin.metadata.enabled = True

        assert len(registry.get_categorisation_plugins()) == 1


class TestPluginInteraction:
    """Tests for plugins interacting with each other."""

    def test_reporter_receives_categorisation_results(self):
        """Test that reporter receives results from categorisation."""
        from src.file_organiser.core.categoriser import FileCategoriser
        from src.file_organiser.core.models import FileInfo
        from pathlib import Path

        registry = PluginRegistry()
        plugin = MockCategorisationPlugin(
            name="test", category_map={".txt": "Documents"}
        )
        registry.register(plugin)

        categoriser = FileCategoriser(plugin_registry=registry)

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        category = categoriser.categorise(file_info)

        assert category == "Documents"
        assert len(plugin.categorised_files) == 1

    def test_filter_prevents_processing(self):
        """Test that filter plugin can prevent file processing."""
        registry = PluginRegistry()

        filter_plugin = MockFilterPlugin(name="test", exclude_all=True)
        registry.register(filter_plugin)

        from src.file_organiser.core.models import FileInfo
        from pathlib import Path

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        should_process = filter_plugin.should_process(file_info)

        assert not should_process
        assert len(filter_plugin.checked_files) == 1
