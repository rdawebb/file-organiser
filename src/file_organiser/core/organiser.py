"""File organiser module to categorise files based on their categories."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, List, Iterator, Union

from .models import MoveResult, MoveStatus, OrganiserResult, OrganiserStats, FileInfo
from .validators import PathValidator

logger = logging.getLogger(__name__)


class FileOrganiser:
    """A class to organise files in a directory into subdirectories based file type"""

    def __init__(
        self,
        directory: Union[str, Path],
        *,
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

        self._collision_cache: dict[Path, set[str]] = {}

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

        files = list(self._discover_files(exclude_patterns or []))

        if not files:
            logger.info("No files found to organise.")
            return OrganiserResult.from_stats(stats, 0.0, dry_run)

        try:
            for file_info in files:
                if self._is_in_category_folder(file_info.path):
                    result = MoveResult(
                        status=MoveStatus.SKIPPED,
                        source=file_info.path,
                        destination=None,
                    )
                    stats.record_result(result)
                    continue

                category = self._categorise_file(file_info)

                result = self._move_file(file_info, category, dry_run)
                stats.record_result(result)

        except KeyboardInterrupt:
            logger.warning("File organisation interrupted by user.")
            raise

        finally:
            duration = time.time() - start_time
            result = OrganiserResult.from_stats(stats, duration, dry_run)

        return result

    def _discover_files(self, exclude_patterns: List[str]) -> Iterator[FileInfo]:
        """Discovers files in the target directory, applying exclusion patterns.

        Args:
            exclude_patterns (List[str]): List of glob patterns to exclude files.

        Yields:
            Iterator[FileInfo]: An iterator of FileInfo objects for discovered files.
        """
        import fnmatch

        for file_path in self.directory.rglob("*"):
            if file_path.is_symlink():
                logger.debug(f"Skipping symlink: {file_path}")
                continue

            if not file_path.is_file():
                continue

            if not self.include_hidden and file_path.name.startswith("."):
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
        categorisers = self.plugins.get_categorisation_plugins()

        for categoriser in categorisers:
            category = categoriser.categorise(file_info)
            if category:
                logger.debug(
                    f"File {file_info.path} categorised as {category} by {categoriser.name}"
                )
                return category

        logger.debug(
            f"File {file_info.path} could not be categorised, defaulting to 'Unknown'"
        )
        return "Unknown"

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

        try:
            PathValidator.validate_category_name(category)

            unique_name = self._get_unique_filename(category_folder, file_info.name)
            dest_path = category_folder / unique_name

            if dry_run:
                logger.info(f"[Dry Run] Would move {file_info.path} to {dest_path}")
                return MoveResult(
                    status=MoveStatus.DRY_RUN,
                    source=file_info.path,
                    destination=dest_path,
                    category=category,
                )

            category_folder.mkdir(parents=True, exist_ok=True)
            file_info.path.rename(dest_path)

            logger.info(f"Moved {file_info.path} to {dest_path}")
            return MoveResult(
                status=MoveStatus.SUCCESS,
                source=file_info.path,
                destination=dest_path,
                category=category,
            )

        except Exception as e:
            logger.error(f"Failed to move {file_info.path} to {category_folder}: {e}")
            return MoveResult(
                status=MoveStatus.FAILED,
                source=file_info.path,
                destination=None,
                error=e,
                category=category,
            )

    def _get_unique_filename(
        self, category_folder: Path, filename: str, max_attempts: int = 10000
    ) -> str:
        """Generates a unique filename with collision avoidance

        Args:
            category_folder (Path): The target category folder.
            filename (str): The original filename.
            max_attempts (int, optional): Maximum attempts to find a unique name. Defaults to 10000.

        Returns:
            str: A unique filename.

        Raises:
            ValueError: If a unique filename cannot be found within max_attempts.
        """
        if category_folder not in self._collision_cache:
            if category_folder.exists():
                self._collision_cache[category_folder] = {
                    entry.name for entry in category_folder.iterdir() if entry.is_file()
                }
            else:
                self._collision_cache[category_folder] = set()

        existing_files = self._collision_cache[category_folder]

        if filename not in existing_files:
            existing_files.add(filename)
            return filename

        path = Path(filename)
        base = path.stem
        extension = path.suffix

        for count in range(1, max_attempts + 1):
            new_filename = f"{base}({count}){extension}"

            if new_filename not in existing_files:
                existing_files.add(new_filename)
                return new_filename

        raise ValueError(
            f"Could not find unique filename for '{filename}' in {category_folder} after {max_attempts} attempts."
        )

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
            known_categories = self.plugins.get_all_categories()

            return parent_name in known_categories

        except ValueError:
            return False
