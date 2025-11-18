"""Models for file organisation results and statistics."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Set, Tuple


class MoveStatus(Enum):
    """Enumeration for file move status."""

    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    DRY_RUN = auto()


@dataclass(frozen=True)
class MoveResult:
    """Data class to hold the result of a file move operation."""

    status: MoveStatus
    source: Path
    destination: Optional[Path]
    error: Optional[Exception] = None
    category: Optional[str] = None

    @property
    def success(self) -> bool:
        """Indicates if the move operation was successful."""
        return self.status == MoveStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Indicates if the move operation failed."""
        return self.status == MoveStatus.FAILED


@dataclass
class OrganiserStats:
    """Data class to track statistics of the file organisation process."""

    files_processed: int = 0
    files_moved: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    unknown_files: int = 0
    errors: List[Tuple[Path, Exception]] = field(default_factory=list)
    categories_used: Set[str] = field(default_factory=set)

    def record_result(self, result: MoveResult) -> None:
        """Updates statistics based on the move result."""
        self.files_processed += 1

        if result.success:
            self.files_moved += 1
            if result.category:
                self.categories_used.add(result.category)
                if result.category == "Unknown":
                    self.unknown_files += 1

        elif result.failed:
            self.files_failed += 1
            if result.error:
                self.errors.append((result.source, result.error))

        elif result.status == MoveStatus.SKIPPED:
            self.files_skipped += 1


@dataclass(frozen=True)
class OrganiserResult:
    """Data class to encapsulate the overall result of a file organisation operation."""

    files_processed: int
    files_moved: int
    files_failed: int
    files_skipped: int
    unknown_files: int
    categories_created: Set[str]
    errors: List[Tuple[Path, Exception]]
    duration_seconds: float
    dry_run: bool = False

    @classmethod
    def from_stats(
        cls, stats: OrganiserStats, duration_seconds: float, dry_run: bool = False
    ) -> "OrganiserResult":
        """Creates an OrganiserResult from OrganiserStats."""
        return cls(
            files_processed=stats.files_processed,
            files_moved=stats.files_moved,
            files_failed=stats.files_failed,
            files_skipped=stats.files_skipped,
            unknown_files=stats.unknown_files,
            categories_created=stats.categories_used.copy(),
            errors=stats.errors.copy(),
            duration_seconds=duration_seconds,
            dry_run=dry_run,
        )

    @property
    def success(self) -> bool:
        """Indicates if the organisation operation was completely successful."""
        return self.files_failed == 0


@dataclass
class FileInfo:
    """Data class to hold information about a file."""

    path: Path
    name: str
    extension: str
    size: int
    modified_time: float

    @classmethod
    def from_path(cls, path: Path) -> "FileInfo":
        """Creates a FileInfo instance from a file path."""
        stat = path.stat()
        return cls(
            path=path,
            name=path.name,
            extension=path.suffix.lower(),
            size=stat.st_size,
            modified_time=stat.st_mtime,
        )
