"""File organiser module to categorise files based on their categories."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator, List, Optional, Union

from .categoriser import FileCategoriser
from .models import FileInfo, MoveResult, MoveStatus, OrganiserResult, OrganiserStats
from .mover import FileMover, MoveOptions
from .validators import PathValidator
from file_organiser.plugins.base import ReporterPlugin
from file_organiser.plugins.registry import PluginRegistry
from file_organiser.utils.logging import get_logger

logger = get_logger(__name__)


class FileOrganiser:
    """A class to organise files in a directory into subdirectories based file type"""

    def __init__(
        self,
        directory: Union[str, Path],
        *,
        plugin_registry: Optional[PluginRegistry] = None,
        reporter: Optional[ReporterPlugin] = None,
        categoriser: Optional[FileCategoriser] = None,
        mover: Optional[FileMover] = None,
        include_hidden: bool = False,
        validate_paths: bool = True,
    ) -> None:
        """Initialises the FileOrganiser with the target directory and options.

        Args:
            directory (Union[str, Path]): The target directory to organise.
            include_hidden (bool, optional): Whether to include hidden files. Defaults to False.
            validate_paths (bool, optional): Whether to validate paths before organising. Defaults to True.
        """
        self.directory = Path(directory).resolve()
        self.include_hidden = include_hidden

        if validate_paths:
            PathValidator.validate_directory(self.directory)
            logger.info(f"Validated directory: {self.directory}")

        self.plugins = plugin_registry or PluginRegistry.create_default()
        self.reporter = reporter or self.plugins.get_default_reporter()
        self.categoriser = categoriser or FileCategoriser(self.plugins)
        self.mover = mover or FileMover(MoveOptions())

        logger.debug(f"FileOrganiser initialised for {self.directory}")

    def organise_files(
        self, *, dry_run: bool = False, exclude_patterns: Optional[List[str]] = None
    ) -> None:
        """Organises files in the target directory

        Args:
            dry_run (bool, optional): If True, simulates the organisation without moving files. Defaults to False.
            exclude_patterns (Optional[List[str]], optional): List of glob patterns to exclude files. Defaults to None.

        Raises:
            KeyboardInterrupt: If the operation is interrupted by the user.
        """
        start_time = time.time()
        stats = OrganiserStats()

        logger.info(
            f"Starting file organisation: {self.directory} "
            f"{'(dry run)' if dry_run else ''}"
        )

        files = list(self._discover_files(exclude_patterns or []))

        if not files:
            logger.info("No files found to organise.")
            return OrganiserResult.from_stats(stats, 0.0, dry_run)

        self.reporter.on_start(total_files=len(files))

        try:
            for file_info in files:
                self.reporter.on_file_processing(file_info)

                if self._is_in_category_folder(file_info.path):
                    result = MoveResult(
                        status=MoveStatus.SKIPPED,
                        source=file_info.path,
                        destination=None,
                    )
                    stats.record_result(result)
                    logger.debug(f"Skipped (already organised): {file_info.path}")
                    continue

                category = self._categorise_file(file_info)

                result = self._move_file(file_info, category, dry_run)
                stats.record_result(result)

                self.reporter.on_file_processed(result)

                if result.success:
                    logger.debug(
                        f"Moved: {file_info.name} -> {category}/{result.destination.name}"
                    )
                else:
                    logger.error(f"Failed to move {file_info.name}: {result.error}")

        except KeyboardInterrupt:
            logger.warning("File organisation interrupted by user.")
            raise

        finally:
            duration = time.time() - start_time
            result = OrganiserResult.from_stats(stats, duration, dry_run)
            self.reporter.on_complete(result)

            logger.info(
                f"Organisation complete: {result.files_moved} files moved, "
                f"{result.files_skipped} files skipped, {result.files_failed} failed "
                f"(Duration: {duration:.2f}s)"
            )

        return result

    def _discover_files(self, exclude_patterns: List[str]) -> Iterator[FileInfo]:
        """Discovers files in the target directory, applying exclusion patterns.

        Args:
            exclude_patterns (List[str]): List of glob patterns to exclude files.

        Yields:
            Iterator[FileInfo]: An iterator of FileInfo objects for discovered files.
        """
        import fnmatch

        logger.debug(f"Discovering files in {self.directory}")

        for file_path in self.directory.rglob("*"):
            if file_path.is_symlink():
                logger.debug(f"Skipping symlink: {file_path}")
                continue

            if not file_path.is_file():
                continue

            if not self.include_hidden and file_path.name.startswith("."):
                logger.debug(f"Skipping hidden file: {file_path}")
                continue

            relative_path = file_path.relative_to(self.directory)
            if any(
                fnmatch.fnmatch(str(relative_path), pattern)
                for pattern in exclude_patterns
            ):
                logger.debug(f"Excluding file by pattern: {file_path}")
                continue

            yield FileInfo.from_path(file_path)

    def _categorise_file(self, file_info: FileInfo) -> str:
        """Determines the category of a file based on type

        Args:
            file_info (FileInfo): The file information object.

        Returns:
            str: The determined category for the file.
        """
        category = self.categoriser.categorise(file_info)

        if category == "unknown":
            logger.debug(f"Could not categorise file: {file_info.name}")
        else:
            logger.debug(f"Categorised file {file_info.name} as {category}")

        return category

    def _move_file(
        self, file_info: FileInfo, category: str, dry_run: bool
    ) -> MoveResult:
        """Moves a file to its category folder

        Args:
            file_info (FileInfo): The file information object.
            category (str): The target category for the file.
            dry_run (bool): If True, does not actually move the file.

        Returns:
            MoveResult: The result of the move operation.

        Raises:
            Exception: If the move operation fails.
        """
        category_folder = self.directory / category

        result = self.mover.move_file(
            source=file_info.path,
            destination_dir=category_folder,
            filename=file_info.name,
            dry_run=dry_run,
            category=category,
        )
        return result

    def _is_in_category_folder(self, file_path: Path) -> bool:
        """Checks if the file is already in a category folder

        Args:
            file_path (Path): The path of the file to check.

        Returns:
            bool: True if the file is in a category folder, False otherwise.

        Raises:
            ValueError: If the file path is not relative to the organiser directory.
        """
        try:
            relative_path = file_path.relative_to(self.directory)

            if len(relative_path.parents) == 1:
                return False

            parent_name = relative_path.parents[-2].name
            known_categories = self.categoriser.get_all_categories()

            return parent_name in known_categories

        except ValueError:
            return False
