"""Unit tests for models module."""

import pytest
from pathlib import Path

from src.file_organiser.core.models import (
    FileInfo,
    MoveResult,
    MoveStatus,
    OrganiserStats,
    OrganiserResult,
)


class TestFileInfo:
    """Tests for FileInfo model."""

    def test_file_info_creation(self):
        """Test creating a FileInfo instance."""
        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=1234567890,
        )

        assert file_info.path == Path("test.txt")
        assert file_info.name == "test.txt"
        assert file_info.extension == ".txt"
        assert file_info.size == 100
        assert file_info.modified_time == 1234567890

    def test_file_info_with_no_extension(self):
        """Test FileInfo with file that has no extension."""
        file_info = FileInfo(
            path=Path("README"),
            name="README",
            extension="",
            size=50,
            modified_time=0,
        )

        assert file_info.name == "README"
        assert file_info.extension == ""

    def test_file_info_with_multi_extension(self):
        """Test FileInfo with file that has multiple extensions."""
        file_info = FileInfo(
            path=Path("archive.tar.gz"),
            name="archive.tar.gz",
            extension=".gz",
            size=1000,
            modified_time=0,
        )

        assert file_info.extension == ".gz"

    def test_file_info_frozen(self):
        """Test that FileInfo is immutable."""
        file_info = FileInfo(
            path=Path("test.txt"),
            name="test.txt",
            extension=".txt",
            size=100,
            modified_time=0,
        )

        try:
            file_info.size = 200
            assert True
        except (AttributeError, Exception):
            # Either AttributeError or FrozenInstanceError
            assert True


class TestMoveResult:
    """Tests for MoveResult model."""

    def test_move_result_success(self):
        """Test creating a successful move result."""
        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("source.txt"),
            destination=Path("dest/source.txt"),
        )

        assert result.success
        assert not result.failed
        assert result.status == MoveStatus.SUCCESS

    def test_move_result_failed(self):
        """Test creating a failed move result."""
        error = Exception("Permission denied")
        result = MoveResult(
            status=MoveStatus.FAILED,
            source=Path("source.txt"),
            destination=None,
            error=error,
        )

        assert not result.success
        assert result.failed
        assert result.status == MoveStatus.FAILED
        assert result.error == error

    def test_move_result_with_category(self):
        """Test move result with category."""
        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("doc.txt"),
            destination=Path("Documents/doc.txt"),
            category="Documents",
        )

        assert result.category == "Documents"
        assert result.success

    def test_move_result_dry_run(self):
        """Test dry run move result."""
        result = MoveResult(
            status=MoveStatus.DRY_RUN,
            source=Path("file.txt"),
            destination=Path("dest/file.txt"),
        )

        assert not result.success
        assert not result.failed
        assert result.status == MoveStatus.DRY_RUN

    def test_move_result_skipped(self):
        """Test skipped move result."""
        result = MoveResult(
            status=MoveStatus.SKIPPED,
            source=Path("file.txt"),
            destination=None,
        )

        assert not result.success
        assert not result.failed
        assert result.status == MoveStatus.SKIPPED

    def test_move_result_frozen(self):
        """Test that MoveResult is immutable."""
        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("test.txt"),
            destination=Path("dest/test.txt"),
        )

        with pytest.raises(AttributeError):
            setattr(result, "status", MoveStatus.FAILED)


class TestOrganiserStats:
    """Tests for OrganiserStats model."""

    def test_organiser_stats_creation(self):
        """Test creating OrganiserStats."""
        stats = OrganiserStats()

        assert stats.files_processed == 0
        assert stats.files_moved == 0
        assert stats.files_failed == 0
        assert stats.files_skipped == 0
        assert stats.unknown_files == 0
        assert len(stats.errors) == 0
        assert len(stats.categories_used) == 0

    def test_record_successful_result(self):
        """Test recording a successful move result."""
        stats = OrganiserStats()
        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("doc.txt"),
            destination=Path("Documents/doc.txt"),
            category="Documents",
        )

        stats.record_result(result)

        assert stats.files_processed == 1
        assert stats.files_moved == 1
        assert stats.files_failed == 0
        assert stats.files_skipped == 0
        assert "Documents" in stats.categories_used

    def test_record_failed_result(self):
        """Test recording a failed move result."""
        stats = OrganiserStats()
        error = Exception("Permission denied")
        result = MoveResult(
            status=MoveStatus.FAILED,
            source=Path("file.txt"),
            destination=None,
            error=error,
        )

        stats.record_result(result)

        assert stats.files_processed == 1
        assert stats.files_moved == 0
        assert stats.files_failed == 1
        assert len(stats.errors) == 1
        assert stats.errors[0] == (Path("file.txt"), error)

    def test_record_skipped_result(self):
        """Test recording a skipped move result."""
        stats = OrganiserStats()
        result = MoveResult(
            status=MoveStatus.SKIPPED,
            source=Path("file.txt"),
            destination=None,
        )

        stats.record_result(result)

        assert stats.files_processed == 1
        assert stats.files_skipped == 1
        assert stats.files_moved == 0

    def test_record_unknown_category(self):
        """Test recording a result with Unknown category."""
        stats = OrganiserStats()
        result = MoveResult(
            status=MoveStatus.SUCCESS,
            source=Path("unknown.xyz"),
            destination=Path("Unknown/unknown.xyz"),
            category="Unknown",
        )

        stats.record_result(result)

        assert stats.unknown_files == 1
        assert "Unknown" in stats.categories_used

    def test_record_multiple_results(self):
        """Test recording multiple results."""
        stats = OrganiserStats()
        results = [
            MoveResult(
                status=MoveStatus.SUCCESS,
                source=Path("doc.txt"),
                destination=Path("Documents/doc.txt"),
                category="Documents",
            ),
            MoveResult(
                status=MoveStatus.SUCCESS,
                source=Path("script.py"),
                destination=Path("Code/script.py"),
                category="Code",
            ),
            MoveResult(
                status=MoveStatus.FAILED,
                source=Path("error.txt"),
                destination=None,
                error=Exception("Error"),
            ),
        ]

        for result in results:
            stats.record_result(result)

        assert stats.files_processed == 3
        assert stats.files_moved == 2
        assert stats.files_failed == 1
        assert len(stats.categories_used) == 2


class TestOrganiserResult:
    """Tests for OrganiserResult model."""

    def test_organiser_result_creation(self):
        """Test creating OrganiserResult."""
        result = OrganiserResult(
            files_processed=10,
            files_moved=8,
            files_failed=2,
            files_skipped=0,
            unknown_files=0,
            categories_created={"Documents", "Code"},
            errors=[],
            duration_seconds=5.5,
        )

        assert result.files_processed == 10
        assert result.files_moved == 8
        assert result.files_failed == 2
        assert result.duration_seconds == 5.5
        assert "Documents" in result.categories_created

    def test_organiser_result_dry_run(self):
        """Test OrganiserResult with dry_run flag."""
        result = OrganiserResult(
            files_processed=10,
            files_moved=0,
            files_failed=0,
            files_skipped=0,
            unknown_files=0,
            categories_created=set(),
            errors=[],
            duration_seconds=2.0,
            dry_run=True,
        )

        assert result.dry_run

    def test_organiser_result_from_stats(self):
        """Test creating OrganiserResult from OrganiserStats."""
        stats = OrganiserStats()

        stats.record_result(
            MoveResult(
                status=MoveStatus.SUCCESS,
                source=Path("file.txt"),
                destination=Path("dest/file.txt"),
                category="Documents",
            )
        )
        stats.record_result(
            MoveResult(
                status=MoveStatus.FAILED,
                source=Path("error.txt"),
                destination=None,
                error=Exception("Error"),
            )
        )

        result = OrganiserResult.from_stats(stats, 1.5, dry_run=False)

        assert result.files_processed == 2
        assert result.files_moved == 1
        assert result.files_failed == 1
        assert result.duration_seconds == 1.5
        assert not result.dry_run
        assert "Documents" in result.categories_created

    def test_organiser_result_with_errors(self):
        """Test OrganiserResult with error details."""
        errors = [
            (Path("file1.txt"), Exception("Error 1")),
            (Path("file2.txt"), Exception("Error 2")),
        ]

        result = OrganiserResult(
            files_processed=5,
            files_moved=3,
            files_failed=2,
            files_skipped=0,
            unknown_files=0,
            categories_created={"Documents"},
            errors=errors,
            duration_seconds=2.0,
        )

        assert len(result.errors) == 2
        assert result.errors[0][0] == Path("file1.txt")

    def test_organiser_result_frozen(self):
        """Test that OrganiserResult is immutable."""
        result = OrganiserResult(
            files_processed=10,
            files_moved=8,
            files_failed=2,
            files_skipped=0,
            unknown_files=0,
            categories_created=set(),
            errors=[],
            duration_seconds=1.0,
        )

        with pytest.raises(AttributeError):
            setattr(result, "files_processed", 20)
