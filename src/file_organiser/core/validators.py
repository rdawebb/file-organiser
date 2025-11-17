"""Validators for file system paths and category names."""

import os
import sys
from pathlib import Path
from typing import Set


class PathValidator:
    """A class to validate file system paths for security and safety."""

    FORBIDDEN_PATHS: Set[Path] = {
        Path("/"),
        Path("/etc"),
        Path("/usr"),
        Path("/bin"),
        Path("/sbin"),
        Path("/boot"),
        Path("/sys"),
        Path("/proc"),
        Path("/dev"),
        Path("/var"),
        Path("/tmp"),
        Path("/System"),  # macOS system folder
    }

    if sys.platform == "win32":
        FORBIDDEN_PATHS.update(
            {
                Path("C:\\"),
                Path("C:\\Windows"),
                Path("C:\\Program Files"),
                Path("C:\\Program Files (x86)"),
                Path("C:\\ProgramData"),
                Path("C:\\Users\\Default"),
                Path("C:\\Users\\Public"),
            }
        )

    @classmethod
    def validate_directory(cls, directory: Path) -> None:
        """
        Validates the given directory path to ensure it is safe to use

        Args:
            directory (Path): The directory path to validate

        Raises:
            FileNotFoundError: If the directory does not exist
            ValueError: If the path is not a directory or is forbidden
            PermissionError: If there are insufficient permissions to access the directory
        """
        directory = directory.resolve()

        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        if not os.access(directory, os.R_OK | os.W_OK):
            raise PermissionError(
                f"Insufficient permissions for directory: {directory}"
            )

        cls._check_forbidden_paths(directory)

        if directory == Path.home():
            raise ValueError(
                "Organising the home directory is not allowed for safety reasons - please choose a subdirectory."
            )

    @classmethod
    def _check_forbidden_paths(cls, directory: Path) -> None:
        """
        Checks if the given directory is in the list of forbidden paths.

        Args:
            directory (Path): The directory path to check.

        Raises:
            ValueError: If the directory is forbidden or contains forbidden paths.
        """
        for forbidden in cls.FORBIDDEN_PATHS:
            try:
                if directory == forbidden:
                    raise ValueError(
                        f"Organising system directories is not allowed: {directory}"
                    )

                if forbidden.is_relative_to(directory):
                    raise ValueError(
                        f"Directory contains system path {forbidden}: {directory}"
                    )

            except (ValueError, AttributeError):
                if str(forbidden).startswith(str(directory) + os.sep):
                    raise ValueError(
                        f"Directory contains system path {forbidden}: {directory}"
                    )

    @classmethod
    def validate_category_name(category: str) -> None:
        """
        Validate that a category name is safe

        Args:
            category (str): The category name to validate

        Raises:
            ValueError: If the category name is invalid
        """
        import re

        if not re.match(r"^[a-z0-9_-]+$", category, re.IGNORECASE):
            raise ValueError(
                f"Invalid category name: '{category}'",
                "Must contain only letters, numbers, underscores, and hyphens.",
            )

        if ".." in category or "/" in category or "\\" in category:
            raise ValueError(
                f"Invalid category name: '{category}'",
                "Category names cannot contain path traversal sequences.",
            )

        if category.startswith(("/", "\\", "~")):
            raise ValueError(
                f"Invalid category name: '{category}'",
                "Category name looks like absolute path.",
            )
