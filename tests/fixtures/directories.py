"""Directory structure utilities for testing."""

from pathlib import Path


def create_organised_directory(base_dir: Path) -> dict:
    """Create a pre-organised directory structure with category folders.

    Args:
        base_dir: Base directory to create structure in

    Returns:
        Dictionary with paths to category folders
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    categories: dict[str, Path] = {
        "Documents": base_dir / "Documents",
        "Code": base_dir / "Code",
        "Images": base_dir / "Images",
        "Videos": base_dir / "Videos",
        "Archives": base_dir / "Archives",
        "Uncategorised": base_dir / "Uncategorised",
    }

    for category_dir in categories.values():
        category_dir.mkdir(parents=True, exist_ok=True)

    return categories


def assert_file_in_directory(file_path: Path, directory: Path) -> bool:
    """Assert that a file is in a directory.

    Args:
        file_path: File to check
        directory: Directory to check in

    Returns:
        True if file is in directory
    """
    try:
        file_path.relative_to(directory)
        return True
    except ValueError:
        return False


def count_files_in_directory(directory: Path, recursive: bool = False) -> int:
    """Count files in a directory.

    Args:
        directory: Directory to count files in
        recursive: If True, count files recursively

    Returns:
        Number of files
    """
    if not directory.exists():
        return 0

    if recursive:
        return len(list(directory.rglob(pattern="*"))) - len(
            list(directory.glob(pattern="*"))
        )
    return len(list(directory.glob(pattern="*")))
