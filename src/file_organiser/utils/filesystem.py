"""Filesystem utilities and abstractions."""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional


class FileSystemAdapter(ABC):
    """Abstract base class for filesystem operations."""

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Checks if a path exists.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        ...

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        """Checks if a path is a file.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path is a file, False otherwise.
        """
        ...

    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        """Checks if a path is a directory.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path is a directory, False otherwise.
        """
        ...

    @abstractmethod
    def list_files(self, directory: Path, recursive: bool = False) -> Iterator[Path]:
        """Lists all files in a directory.

        Args:
            directory (Path): The directory to list files from.
            recursive (bool): Whether to list files recursively.

        Returns:
            Iterator[Path]: An iterator over file paths in the directory.
        """
        ...

    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> None:
        """Moves a file from source to destination.

        Args:
            source (Path): The source file path.
            destination (Path): The destination file path.
        """
        ...

    @abstractmethod
    def create_directory(self, path: Path, parents: bool = True) -> None:
        """Creates a directory at the specified path.

        Args:
            path (Path): The directory path to create.
        """
        ...

    @abstractmethod
    def get_size(self, path: Path) -> int:
        """Gets the size of a file in bytes.

        Args:
            path (Path): The file path.

        Returns:
            int: The size of the file in bytes.
        """
        ...

    @abstractmethod
    def get_modified_time(self, path: Path) -> float:
        """Gets the last modified time of a file.

        Args:
            path (Path): The file path.

        Returns:
            float: The last modified time as a timestamp.
        """
        ...


class RealFileSystem(FileSystemAdapter):
    """Real filesystem implementation of FileSystemAdapter."""

    def exists(self, path: Path) -> bool:
        """Checks if a path exists."""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Checks if a path is a file."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Checks if a path is a directory."""
        return path.is_dir()

    def list_files(self, directory: Path, recursive: bool = False) -> Iterator[Path]:
        """Lists all files in a directory."""
        if recursive:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    yield file_path
        else:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    yield file_path

    def move_file(self, source: Path, destination: Path) -> None:
        """Moves a file from source to destination."""
        shutil.move(str(source), str(destination))

    def create_directory(self, path: Path, parents: bool = True) -> None:
        """Creates a directory at the specified path."""
        path.mkdir(parents=parents, exist_ok=True)

    def get_size(self, path: Path) -> int:
        """Gets the size of a file in bytes."""
        return path.stat().st_size

    def get_modified_time(self, path: Path) -> float:
        """Gets the last modified time of a file."""
        return path.stat().st_mtime


class InMemoryFileSystem(FileSystemAdapter):
    """In-memory filesystem implementation of FileSystemAdapter for testing purposes."""

    def __init__(self):
        """Initialises the empty in-memory filesystem."""
        self.files: dict[Path, bytes] = {}
        self.directories: set[Path] = {Path("/")}

    def exists(self, path: Path) -> bool:
        """Checks if a path exists."""
        return path in self.files or path in self.directories

    def is_file(self, path: Path) -> bool:
        """Checks if a path is a file."""
        return path in self.files

    def is_dir(self, path: Path) -> bool:
        """Checks if a path is a directory."""
        return path in self.directories

    def list_files(self, directory: Path, recursive: bool = False) -> Iterator[Path]:
        """Lists all files in a directory."""
        for file_path in self.files.keys():
            if recursive:
                try:
                    file_path.relative_to(directory)
                    yield file_path
                except ValueError:
                    continue
            else:
                if file_path.parent == directory:
                    yield file_path

    def move_file(self, source: Path, destination: Path) -> None:
        """Moves a file from source to destination."""
        if source not in self.files:
            raise FileNotFoundError(f"Source file does not exist: {source}")

        self.files[destination] = self.files.pop(source)
        self.directories.add(destination.parent)

    def create_directory(self, path: Path, parents: bool = True) -> None:
        """Creates a directory at the specified path."""
        if parents:
            for parent in path.parents:
                self.directories.add(parent)
        self.directories.add(path)

    def get_size(self, path: Path) -> int:
        """Gets the size of a file in bytes."""
        if path not in self.files:
            raise FileNotFoundError(f"File does not exist: {path}")
        return len(self.files[path])

    def get_modified_time(self, path: Path) -> float:
        """Gets the last modified time of a file."""
        import time

        return time.time()  # Simplified for in-memory filesystem

    def add_file(self, path: Path, content: bytes = b"") -> None:
        """Adds a file to the in-memory filesystem.

        Args:
            path (Path): The file path.
            content (bytes): The content of the file.
        """
        self.files[path] = content
        self.directories.add(path.parent)

    def clear(self) -> None:
        """Clears the in-memory filesystem."""
        self.files.clear()
        self.directories = {Path("/")}


def get_file_info(path: Path, fs: Optional[FileSystemAdapter] = None) -> dict:
    """Gets basic file information.

    Args:
        path (Path): The file path.
        fs (Optional[FileSystemAdapter]): The filesystem adapter to use. Defaults to RealFileSystem.

    Returns:
        dict: A dictionary containing file information.
    """
    if fs is None:
        fs = RealFileSystem()

    return {
        "path": path,
        "name": path.name,
        "stem": path.stem,
        "extension": path.suffix.lower(),
        "size": fs.get_size(path) if fs.is_file(path) else None,
        "modified_time": fs.get_modified_time(path) if fs.is_file(path) else None,
        "exists": fs.exists(path),
        "is_file": fs.is_file(path),
    }


def safe_delete(path: Path, fs: Optional[FileSystemAdapter] = None) -> bool:
    """Safely deletes a file.

    Args:
        path (Path): The file path to delete.
        fs (Optional[FileSystemAdapter]): The filesystem adapter to use. Defaults to RealFileSystem.
    """
    try:
        if fs is None:
            path.unlink()
        else:
            pass  # Not implemented for custom filesystem adapters
        return True
    except Exception:
        return False


def get_directory_size(directory: Path, fs: Optional[FileSystemAdapter] = None) -> int:
    """Calculates the total size of all files in a directory.

    Args:
        directory (Path): The directory path.
        fs (Optional[FileSystemAdapter]): The filesystem adapter to use. Defaults to RealFileSystem.

    Returns:
        int: The total size of files in bytes.
    """
    if fs is None:
        fs = RealFileSystem()

    total_size = 0
    for file_path in fs.list_files(directory, recursive=True):
        total_size += fs.get_size(file_path)

    return total_size
