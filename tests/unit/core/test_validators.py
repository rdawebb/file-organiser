"""Unit tests for validators module."""

import pytest
from pathlib import Path

from src.file_organiser.core.validators import PathValidator


class TestPathValidation:
    """Tests for path validation."""

    def test_validate_directory_valid(self, tmp_path):
        """Test validating an existing directory."""
        # Should not raise
        PathValidator.validate_directory(tmp_path)

    def test_validate_directory_invalid(self):
        """Test validating a non-existent directory."""
        invalid_path = Path("/nonexistent/path/to/directory")

        with pytest.raises(FileNotFoundError):
            PathValidator.validate_directory(invalid_path)

    def test_validate_directory_file_not_dir(self, tmp_path):
        """Test validating a file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(NotADirectoryError):
            PathValidator.validate_directory(file_path)

    def test_validate_directory_with_string_path(self, tmp_path):
        """Test validating directory with Path object."""
        # Should not raise
        PathValidator.validate_directory(tmp_path)


class TestCategoryNameValidation:
    """Tests for category name validation."""

    def test_validate_category_name_valid(self):
        """Test validating a valid category name."""
        # Should not raise
        PathValidator.validate_category_name("Documents")
        PathValidator.validate_category_name("My_Documents")
        PathValidator.validate_category_name("Category-123")

    def test_validate_category_name_with_slash(self):
        """Test validating category name with slash."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("bad/name")

    def test_validate_category_name_with_backslash(self):
        """Test validating category name with backslash."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("bad\\name")

    def test_validate_category_name_parent_directory(self):
        """Test validating category name with parent directory reference."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("..")

    def test_validate_category_name_current_directory(self):
        """Test validating category name with current directory reference."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name(".")

    def test_validate_category_name_absolute_path(self):
        """Test validating category name as absolute path."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("/absolute/path")

    def test_validate_category_name_empty(self):
        """Test validating empty category name."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("")

    def test_validate_category_name_with_newline(self):
        """Test validating category name with newline."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("bad\nname")

    def test_validate_category_name_with_null(self):
        """Test validating category name with null character."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("bad\0name")

    def test_validate_category_name_spaces(self):
        """Test validating category name with spaces."""
        # Should be valid - spaces are allowed
        PathValidator.validate_category_name("My Category")


class TestFilePathValidation:
    """Tests for file permissions validation."""

    def test_validate_directory_writable_with_file(self, tmp_path):
        """Test that directory validation checks write access."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert test_file.exists()
        # Should not raise
        PathValidator.validate_directory(tmp_path)


class TestPathTraversalProtection:
    """Tests for path traversal attack prevention."""

    def test_validate_path_traversal_attempt(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("../../../etc/passwd")

    def test_validate_path_normalization(self):
        """Test that normalized paths are validated correctly."""
        # Path with multiple slashes should fail
        with pytest.raises(ValueError):
            PathValidator.validate_category_name("path//to//directory")


class TestPermissionValidation:
    """Tests for permission validation."""

    def test_validate_directory_readable(self, tmp_path):
        """Test validating directory is readable."""
        # Should not raise
        PathValidator.validate_directory(tmp_path)
        assert tmp_path.exists()
