"""Handles moving files with safety checks and options."""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import MoveResult, MoveStatus
from file_organiser.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MoveOptions:
    """Configuration options for moving files."""

    atomic: bool = True  # use atomic move operations
    verify_checksum: bool = True  # verify file integrity after move
    preserve_metadata: bool = True  # preserve permissions and timestamps
    create_dirs: bool = True  # create target directories automatically
    overwrite_existing: bool = False  # overwrite existing files


class FileMover:
    """Handles moving files with specified options and safety checks."""

    def __init__(self, options: MoveOptions) -> None:
        """Initialises the FileMover with given options.

        Args:
            options (MoveOptions): Configuration options for moving files.
        """
        self.options = options or MoveOptions()
        self._collision_cache: dict[Path, set[str]] = {}

    def move_file(
        self,
        source: Path,
        destination_dir: Path,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        dry_run: bool = False,
    ) -> MoveResult:
        """Moves a file to the specified destination directory.

        Args:
            source (Path): The source file path
            destination_dir (Path): The target directory path
            filename (Optional[str], optional): The target filename - use source if None
            dry_run (bool, optional): If True, simulates the move without performing it

        Returns:
            MoveResult: The result of the move operation.
        """
        try:
            if not source.exists():
                raise FileNotFoundError(f"Source file does not exist: {source}")
            if not source.is_file():
                raise ValueError(f"Source path is not a file: {source}")

            if filename is None:
                filename = source.name

            unique_filename = self._get_unique_filename(destination_dir, filename)
            dest = destination_dir / unique_filename

            if dry_run:
                logger.info(f"[Dry Run] Moving {source} to {dest}")
                return MoveResult(
                    status=MoveStatus.DRY_RUN,
                    source=source,
                    destination=dest,
                    category=category,
                )

            if self.options.create_dirs:
                destination_dir.mkdir(parents=True, exist_ok=True)

            if self.options.atomic:
                self._atomic_move(source, dest)
            else:
                shutil.move(str(source), str(dest))

            if self.options.verify_checksum:
                if not self._verify_move(source, dest):
                    raise ValueError("File integrity check failed after move.")

            logger.debug(f"Moved {source.name} -> {dest}")
            return MoveResult(
                status=MoveStatus.SUCCESS,
                source=source,
                destination=dest,
                category=category,
            )

        except PermissionError as e:
            logger.error(f"Permission denied moving {source.name}: {e}")
            self._invalidate_cache(destination_dir)
            return MoveResult(
                status=MoveStatus.FAILED,
                source=source,
                destination=None,
                error=e,
                category=category,
            )

        except (OSError, IOError, shutil.Error) as e:
            logger.error(f"Error moving {source.name}: {e}")
            self._invalidate_cache(destination_dir)
            return MoveResult(
                status=MoveStatus.FAILED,
                source=source,
                destination=None,
                error=e,
                category=category,
            )

        except Exception as e:
            logger.error(f"Unexpected error moving {source.name}: {e}")
            self._invalidate_cache(destination_dir)
            return MoveResult(
                status=MoveStatus.FAILED,
                source=source,
                destination=None,
                error=e,
                category=category,
            )

    def _atomic_move(self, source: Path, dest: Path) -> None:
        """Performs an atomic move operation.

        Args:
            source (Path): The source file path.
            dest (Path): The destination file path.
        """
        try:
            source.rename(dest)
            logger.debug(f"Atomic rename: {source} -> {dest}")
        except OSError:
            logger.debug(f"Cross-filesystem move: {source} -> {dest}")
            temp_dest = dest.with_suffix(dest.suffix + ".tmp")

            try:
                if self.options.preserve_metadata:
                    shutil.copy2(str(source), str(temp_dest))
                else:
                    shutil.copy(str(source), str(temp_dest))

                temp_dest.rename(dest)
                source.unlink()

            except Exception:
                if temp_dest.exists():
                    temp_dest.unlink()
                raise

    def _verify_move(self, source: Path, dest: Path) -> bool:
        """Verifies that the source and destination files are identical.

        Args:
            source (Path): The source file path.
            dest (Path): The destination file path.

        Returns:
            bool: True if files are identical, False otherwise.
        """
        import hashlib

        def file_checksum(path: Path) -> str:
            """Calculates the SHA256 checksum of a file."""
            hash = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash.update(chunk)
            return hash.hexdigest()

        if not source.exists() and dest.exists():
            return True

        try:
            source_hash = file_checksum(source)
            dest_hash = file_checksum(dest)
            return source_hash == dest_hash
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False

    def _get_unique_filename(
        self, directory: Path, filename: str, max_attempts: int = 10000
    ) -> str:
        """Generates a unique filename with collision avoidance

        Args:
            directory (Path): The target category folder.
            filename (str): The original filename.
            max_attempts (int): Maximum attempts to find a unique name. Defaults to 10000.

        Returns:
            str: A unique filename.
        """
        if directory not in self._collision_cache:
            if directory.exists():
                self._collision_cache[directory] = {
                    entry.name for entry in directory.iterdir() if entry.is_file()
                }
            else:
                self._collision_cache[directory] = set()

        existing_files = self._collision_cache[directory]

        if filename not in existing_files:
            existing_files.add(filename)
            return filename

        path = Path(filename)
        base = path.stem
        extension = path.suffix

        for count in range(1, max_attempts + 1):
            new_filename = f"{base}({count}){extension}"

            if len(new_filename.encode("utf-8")) > 255:
                max_base_length = 255 - len(f"({count}){extension}".encode("utf-8"))
                base = base[:max_base_length]
                new_filename = f"{base}({count}){extension}"

            if new_filename not in existing_files:
                existing_files.add(new_filename)
                return new_filename

        raise ValueError(
            f"Unable to generate unique filename for '{filename}' after {max_attempts} attempts."
        )

    def _invalidate_cache(self, directory: Path) -> None:
        """Invalidates the collision cache for a given directory.

        Args:
            directory (Path): The directory whose cache should be invalidated.
        """
        self._collision_cache.pop(directory, None)
        logger.debug(f"Invalidated collision cache for {directory}")

    def clear_cache(self) -> None:
        """Clears the entire collision cache."""
        self._collision_cache.clear()
        logger.debug("Cleared entire collision cache")
