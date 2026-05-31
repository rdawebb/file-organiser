"""Handles moving files with safety checks and options."""

from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Optional

from file_mover import file_mover

from src.file_organiser.utils.logging import get_logger

from .models import MoveResult, MoveStatus

logger: Logger = get_logger(name=__name__)


def _result_to_move_result(result: file_mover.MoveResult) -> MoveResult:
    """Converts a Rust MoveResult into a Python MoveResult.

    Args:
        result (file_mover.MoveResult): The Rust MoveResult to convert.

    Returns:
        MoveResult: The converted Python MoveResult.
    """
    status_map: dict[str, MoveStatus] = {
        "SUCCESS": MoveStatus.SUCCESS,
        "FAILED": MoveStatus.FAILED,
        "SKIPPED": MoveStatus.SKIPPED,
        "DRY_RUN": MoveStatus.DRY_RUN,
    }

    status_str = str(object=result.status)
    if "." in status_str:
        status_str: str = status_str.split(sep=".")[-1]
    status: MoveStatus = status_map.get(status_str, MoveStatus.FAILED)

    source = Path(result.source)
    destination: Path | None = Path(result.destination) if result.destination else None
    error: Exception | None = Exception(result.error) if result.error else None
    category: str = result.category

    return MoveResult(
        status=status,
        source=source,
        destination=destination,
        error=error,
        category=category,
    )


@dataclass
class MoveOptions:
    """Configuration options for moving files."""

    atomic: bool = True  # use atomic move operations
    verify_checksum: bool = True  # verify file integrity after move
    preserve_metadata: bool = True  # preserve permissions and timestamps
    create_dirs: bool = True  # create target directories automatically
    overwrite_existing: bool = False  # overwrite existing files


class FileMover:
    """Handles file moving operations via Rust backend."""

    def __init__(self, options: MoveOptions) -> None:
        """Initialises the FileMover with given options.

        Args:
            options (MoveOptions): The options to configure the file mover.
        """
        self.options: MoveOptions = options or MoveOptions()
        py_options: MoveResult = file_mover.MoveOptions(
            atomic=self.options.atomic,
            verify_checksum=self.options.verify_checksum,
            preserve_metadata=self.options.preserve_metadata,
            create_dirs=self.options.create_dirs,
            overwrite_existing=self.options.overwrite_existing,
        )
        self.mover: file_mover.FileMover = file_mover.FileMover(options=py_options)

    def move_file(
        self,
        source: Path,
        destination: Path,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        dry_run: bool = False,
    ) -> MoveResult:
        """Moves a file from source to destination.

        Args:
            source (Path): The source file path.
            destination (Path): The destination file path.
            filename (Optional[str]): The new filename (if renaming).
            category (Optional[str]): The category to move the file into.
            dry_run (bool): If True, perform a trial run without making changes.

        Returns:
            MoveResult: The result of the move operation.
        """
        result: MoveResult = self.mover.move_file(
            str(object=source),
            str(object=destination),
            filename=filename,
            category=category,
            dry_run=dry_run,
        )

        py_result: MoveResult = _result_to_move_result(result)

        return py_result

    def move_files_batch(
        self,
        sources: list[Path],
        destination: Path,
        category: Optional[str] = None,
        dry_run: bool = False,
    ) -> list[MoveResult]:
        """Moves multiple files from sources to destination.

        Args:
            sources (list[Path]): The list of source file paths.
            destination (Path): The destination directory path.
            category (Optional[str]): The category to move the files into.
            dry_run (bool): If True, perform a trial run without making changes.

        Returns:
            MoveResult: The result of the move operation.
        """
        raw_results = self.mover.move_files_batch(
            [str(s) for s in sources],
            str(destination),
            category=category,
            dry_run=dry_run,
        )

        py_results: list[MoveResult] = [_result_to_move_result(r) for r in raw_results]

        if any(r.failed for r in py_results):
            raise IOError(py_results[0].error)

        return py_results

    def clear_cache(self) -> None:
        """Clears the file mover's cache."""
        self.mover.clear_cache()
