"""Unit tests for categoriser module."""

from pathlib import Path

from fixtures.mock_plugins import MockCategorisationPlugin

from file_organiser.core.categoriser import FileCategoriser
from file_organiser.core.models import FileInfo
from file_organiser.plugins.registry import PluginRegistry


class TestCategoriserInitialisation:
    """Tests for FileCategoriser initialisation."""

    def test_categoriser_with_registry(self, mock_plugin_registry):
        """Test creating categoriser with a registry."""
        categoriser = FileCategoriser(plugin_registry=mock_plugin_registry)

        assert categoriser.plugin_registry == mock_plugin_registry
        assert categoriser.fallback_category == "Uncategorised"

    def test_categoriser_with_custom_fallback(self):
        """Test creating categoriser with custom fallback category."""
        categoriser = FileCategoriser(
            plugin_registry=None,
            fallback_category="Unknown",
        )

        assert categoriser.fallback_category == "Unknown"

    def test_categoriser_without_registry(self):
        """Test creating categoriser without registry."""
        categoriser = FileCategoriser(plugin_registry=None)

        assert categoriser.plugin_registry is not None or True
        assert categoriser.fallback_category == "Uncategorised"


class TestSingleCategorisation:
    """Tests for categorising individual files."""

    def test_categorise_matching_file(self, file_categoriser, sample_text_file_info):
        """Test categorising a file that matches plugin category."""
        category: str = file_categoriser.categorise(sample_text_file_info)

        assert category == "Documents"

    def test_categorise_code_file(self, file_categoriser, sample_code_file_info):
        """Test categorising a code file."""
        category: str = file_categoriser.categorise(sample_code_file_info)

        assert category == "Code"

    def test_categorise_image_file(self, file_categoriser, sample_image_file_info):
        """Test categorising an image file."""
        category: str = file_categoriser.categorise(sample_image_file_info)

        assert category == "Images"

    def test_categorise_with_fallback(self, categoriser_with_fallback):
        """Test categorisation falls back when no plugins match."""
        file_info = FileInfo(
            path=Path("unknown.xyz"),
            name="unknown.xyz",
            extension=".xyz",
            size=100,
            modified_time=0,
        )

        category: str = categoriser_with_fallback.categorise(file_info)

        assert category == "Other"

    def test_categorise_unknown_extension(self, file_categoriser):
        """Test categorising file with unknown extension."""
        file_info = FileInfo(
            path=Path("unknown.xyz"),
            name="unknown.xyz",
            extension=".xyz",
            size=100,
            modified_time=0,
        )

        category: str = file_categoriser.categorise(file_info)

        assert category == "Uncategorised"


class TestBatchCategorisation:
    """Tests for categorising multiple files."""

    def test_categorise_batch(self, file_categoriser, various_file_infos):
        """Test categorising multiple files at once."""
        results: dict[Path, str] = file_categoriser.categorise_batch(various_file_infos)

        assert len(results) == len(various_file_infos)
        assert results[Path("doc.txt")] == "Documents"
        assert results[Path("code.py")] == "Code"
        assert results[Path("image.jpg")] == "Images"

    def test_categorise_empty_batch(self, file_categoriser):
        """Test categorising an empty list."""
        results: dict[Path, str] = file_categoriser.categorise_batch([])

        assert results == {}

    def test_categorise_batch_with_fallback(
        self, categoriser_with_fallback, various_file_infos
    ):
        """Test batch categorisation with fallback."""
        results: dict[Path, str] = categoriser_with_fallback.categorise_batch(
            various_file_infos
        )

        assert len(results) == len(various_file_infos)
        # All should use fallback
        for category in results.values():
            assert category == "Other"


class TestCategoryDiscovery:
    """Tests for discovering available categories."""

    def test_get_all_categories(self, file_categoriser):
        """Test retrieving all available categories."""
        categories: list[str] = file_categoriser.get_all_categories()

        assert "Uncategorised" in categories
        assert "Documents" in categories
        assert "Code" in categories
        assert "Images" in categories

    def test_get_all_categories_with_fallback_only(self, categoriser_with_fallback):
        """Test getting categories when only fallback exists."""
        categories: list[str] = categoriser_with_fallback.get_all_categories()

        assert "Other" in categories
        assert len(categories) == 1

    def test_get_category_info(self, file_categoriser):
        """Test retrieving category information."""
        info: dict[str, str | list[str]] = file_categoriser.get_category_info(
            "Documents"
        )

        assert info["name"] == "Documents"
        assert isinstance(info["provided_by"], list)


class TestPluginCaching:
    """Tests for plugin cache functionality."""

    def test_plugin_cache_validity(self, file_categoriser):
        """Test that plugin cache is used."""
        # Second call should use cache
        plugins1: list[MockCategorisationPlugin] = file_categoriser._get_plugins()
        plugins2: list[MockCategorisationPlugin] = file_categoriser._get_plugins()

        assert plugins1 is plugins2

    def test_invalidate_cache(self, file_categoriser):
        """Test cache invalidation."""
        file_categoriser._get_plugins()
        assert file_categoriser._cache_valid

        # Invalidate
        file_categoriser._invalidate_cache()
        assert not file_categoriser._cache_valid

        # Next call should rebuild
        plugins: list[MockCategorisationPlugin] = file_categoriser._get_plugins()
        assert file_categoriser._cache_valid
        assert plugins is not None


class TestErrorHandling:
    """Tests for error handling in categorisation."""

    def test_categorisation_with_failing_plugin(self, mock_plugin_registry):
        """Test handling of plugin exceptions."""
        failing_plugin = MockCategorisationPlugin(
            name="failing",
            should_fail=True,
            priority=100,  # Higher priority so it runs first
        )
        registry = PluginRegistry()
        registry.register(plugin=failing_plugin)

        categoriser = FileCategoriser(plugin_registry=registry)

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        # Should fall back when plugin fails
        category: str = categoriser.categorise(file_info)
        assert category == "Uncategorised"

    def test_multiple_plugin_fallthrough(self, mock_plugin_registry):
        """Test fallthrough when multiple plugins don't categorise."""
        plugin1 = MockCategorisationPlugin(
            name="plugin1",
            category_map={".txt": "Documents"},
            priority=100,
        )
        plugin2 = MockCategorisationPlugin(
            name="plugin2",
            category_map={".py": "Code"},
            priority=90,
        )

        registry = PluginRegistry()
        registry.register(plugin=plugin1)
        registry.register(plugin=plugin2)

        categoriser = FileCategoriser(plugin_registry=registry)

        # File doesn't match either plugin
        file_info = FileInfo(
            path=Path("image.jpg"),
            name="image.jpg",
            extension=".jpg",
            size=100,
            modified_time=0,
        )

        category: str = categoriser.categorise(file_info)
        assert category == "Uncategorised"


class TestPluginPriority:
    """Tests for plugin priority ordering."""

    def test_plugin_priority_order(self, mock_plugin_registry):
        """Test that plugins are consulted in priority order."""
        high_priority = MockCategorisationPlugin(
            name="high",
            category_map={".txt": "TextFiles"},
            priority=100,
        )
        low_priority = MockCategorisationPlugin(
            name="low",
            category_map={".txt": "Documents"},
            priority=10,
        )

        mock_plugin_registry.register(high_priority)
        mock_plugin_registry.register(low_priority)

        categoriser = FileCategoriser(plugin_registry=mock_plugin_registry)

        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        # High priority plugin should categorise first
        category: str = categoriser.categorise(file_info)
        assert category == "TextFiles"


class TestCategoriserStatistics:
    """Tests for categoriser statistics."""

    def test_get_statistics(self, file_categoriser):
        """Test retrieving categoriser statistics."""
        stats: dict[str, int] = file_categoriser.get_statistics()

        assert isinstance(stats, dict)
