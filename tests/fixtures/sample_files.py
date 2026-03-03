"""Sample file generators and utilities for testing."""

from pathlib import Path
from typing import List


def create_sample_files(
    directory: Path, file_specs: List[tuple[str, str]]
) -> List[Path]:
    """Create sample files in a directory.

    Args:
        directory: Target directory to create files in
        file_specs: List of (filename, content) tuples

    Returns:
        List of created file paths
    """
    directory.mkdir(parents=True, exist_ok=True)
    created_files = []

    for filename, content in file_specs:
        file_path = directory / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        created_files.append(file_path)

    return created_files


def create_test_structure(base_dir: Path) -> dict:
    """Create a complete test directory structure with various file types.

    Args:
        base_dir: Base directory to create structure in

    Returns:
        Dictionary with paths to various file types
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    structure = {
        "documents": [],
        "images": [],
        "videos": [],
        "code": [],
        "archives": [],
        "text": [],
    }

    # Document files
    structure["documents"] = create_sample_files(
        base_dir / "source",
        [
            ("report.pdf", "%PDF-1.4 fake pdf content"),
            ("presentation.docx", "PK\x03\x04 fake docx"),
            ("spreadsheet.xlsx", "PK\x03\x04 fake xlsx"),
        ],
    )

    # Image files
    structure["images"] = create_sample_files(
        base_dir / "source",
        [
            ("photo.jpg", "\xff\xd8\xff fake jpg"),
            ("image.png", "\x89PNG\r\n fake png"),
            ("graphic.svg", "<?xml version='1.0'?>"),
        ],
    )

    # Video files
    structure["videos"] = create_sample_files(
        base_dir / "source",
        [
            ("movie.mp4", "ftypisom fake mp4"),
            ("clip.mkv", "\x1a\x45\xdf\xa3 fake mkv"),
        ],
    )

    # Code files
    structure["code"] = create_sample_files(
        base_dir / "source",
        [
            ("script.py", "print('hello')"),
            ("styles.css", "body { color: red; }"),
            ("page.js", "console.log('hi');"),
        ],
    )

    # Archive files
    structure["archives"] = create_sample_files(
        base_dir / "source",
        [
            ("archive.zip", "PK\x03\x04 fake zip"),
            ("compressed.tar.gz", "\x1f\x8b fake tar.gz"),
        ],
    )

    # Text files
    structure["text"] = create_sample_files(
        base_dir / "source",
        [
            ("readme.txt", "This is a readme file"),
            ("notes.md", "# Notes"),
        ],
    )

    return structure


def create_problematic_files(directory: Path) -> dict:
    """Create files with special or problematic names for edge case testing.

    Args:
        directory: Target directory

    Returns:
        Dictionary with paths to problematic files
    """
    directory.mkdir(parents=True, exist_ok=True)

    files = {}

    # Files with special characters
    try:
        files["special_chars"] = (directory / "file with spaces.txt").write_text("test")
    except Exception:
        pass

    try:
        files["unicode"] = (directory / "файл_日本語.txt").write_text("unicode test")
    except Exception:
        pass

    # Hidden files
    files["hidden"] = (directory / ".hidden_file").write_text("hidden")

    # Files with multiple extensions
    files["multi_ext"] = (directory / "archive.tar.gz").write_text("multi-ext")

    # Very long filename (within filesystem limits)
    long_name = "a" * 100 + ".txt"
    try:
        files["long_name"] = (directory / long_name).write_text("long")
    except Exception:
        pass

    return files
