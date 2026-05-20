"""Unit tests for organiser module."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from file_organiser.core.models import FileInfo

from src.file_organiser.core.models import OrganiserResult
from src.file_organiser.core.organiser import FileOrganiser
from tests.fixtures.mock_plugins import MockReporterPlugin


class TestFileOrganiserInitialisation:
    """Tests for FileOrganiser initialisation."""

    def test_organiser_creation(self, tmp_unorganised_dir):
        """Test creating a FileOrganiser instance."""
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            include_hidden=False,
            validate_paths=False,
        )

        assert organiser.directory == tmp_unorganised_dir
        assert not organiser.include_hidden

    def test_organiser_with_reporter(self, tmp_unorganised_dir):
        """Test creating organiser with custom reporter."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        assert organiser.reporter == reporter

    def test_organiser_with_validation(self, tmp_unorganised_dir):
        """Test creating organiser with path validation."""
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            validate_paths=True,
        )

        assert organiser.directory is not None

    def test_organiser_with_hidden_files(self, tmp_path):
        """Test creating organiser that includes hidden files."""
        (tmp_path / ".hidden").write_text("hidden")

        organiser = FileOrganiser(
            directory=tmp_path,
            include_hidden=True,
            validate_paths=False,
        )

        assert organiser.include_hidden


class TestFileOrganisation:
    """Tests for file organisation functionality."""

    def test_organise_files_dry_run(self, tmp_unorganised_dir):
        """Test dry run file organisation."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert isinstance(result, OrganiserResult)
        assert result.dry_run
        assert result.files_processed > 0

    def test_organise_files_with_exclude_patterns(self, tmp_unorganised_dir):
        """Test file organisation with exclude patterns."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(
            dry_run=True,
            exclude_patterns=["*.txt"],
        )

        assert isinstance(result, OrganiserResult)

    def test_organise_empty_directory(self, tmp_path):
        """Test organising an empty directory."""
        empty_dir: Path = tmp_path / "empty"
        empty_dir.mkdir()

        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=empty_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert result.files_processed == 0

    def test_organise_files_returns_result(self, tmp_unorganised_dir):
        """Test that organise_files returns proper result."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert hasattr(result, "files_processed")
        assert hasattr(result, "files_moved")
        assert hasattr(result, "files_failed")
        assert hasattr(result, "duration_seconds")
        assert result.duration_seconds >= 0


class TestReporterIntegration:
    """Tests for reporter plugin integration."""

    def test_reporter_on_start_called(self, tmp_unorganised_dir):
        """Test that reporter.on_start is called."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        organiser.organise_files(dry_run=True)

        assert reporter.start_called
        assert reporter.total_files > 0

    def test_reporter_on_complete_called(self, tmp_unorganised_dir):
        """Test that reporter.on_complete is called."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        organiser.organise_files(dry_run=True)

        assert reporter.complete_called
        assert reporter.complete_result is not None

    def test_reporter_on_file_processing_called(self, tmp_unorganised_dir):
        """Test that reporter.on_file_processing is called for each file."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        organiser.organise_files(dry_run=True)

        assert len(reporter.processing_files) > 0

    def test_reporter_on_file_processed_called(self, tmp_unorganised_dir):
        """Test that reporter.on_file_processed is called for each file."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        organiser.organise_files(dry_run=True)

        # Should have processed results
        assert len(reporter.processed_results) > 0


class TestFileDiscovery:
    """Tests for file discovery functionality."""

    def test_discover_files_in_directory(self, tmp_unorganised_dir):
        """Test discovering files in directory."""
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            include_hidden=False,
            validate_paths=False,
        )

        files: list[FileInfo] = list(organiser._discover_files(exclude_patterns=[]))

        assert len(files) > 0

    def test_discover_excludes_hidden_files(self, tmp_path):
        """Test that hidden files are excluded by default."""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden").write_text("hidden")

        organiser = FileOrganiser(
            directory=tmp_path,
            include_hidden=False,
            validate_paths=False,
        )

        files: list[FileInfo] = list(organiser._discover_files(exclude_patterns=[]))
        file_names: list[str] = [f.name for f in files]

        assert "visible.txt" in file_names
        assert ".hidden" not in file_names

    def test_discover_includes_hidden_files(self, tmp_path):
        """Test that hidden files are included when requested."""
        (tmp_path / "visible.txt").write_text("visible")
        (tmp_path / ".hidden").write_text("hidden")

        organiser = FileOrganiser(
            directory=tmp_path,
            include_hidden=True,
            validate_paths=False,
        )

        files: list[FileInfo] = list(organiser._discover_files(exclude_patterns=[]))
        file_names: list[str] = [f.name for f in files]

        assert "visible.txt" in file_names
        assert ".hidden" in file_names

    def test_discover_respects_exclude_patterns(self, tmp_path):
        """Test that exclude patterns are respected."""
        (tmp_path / "file.txt").write_text("text")
        (tmp_path / "script.py").write_text("python")
        (tmp_path / "readme.md").write_text("markdown")

        organiser = FileOrganiser(
            directory=tmp_path,
            validate_paths=False,
        )

        files: list[FileInfo] = list(
            organiser._discover_files(exclude_patterns=["*.txt"])
        )
        file_names: list[str] = [f.name for f in files]

        assert "file.txt" not in file_names
        assert "script.py" in file_names
        assert "readme.md" in file_names


class TestOrganisationResult:
    """Tests for organisation result handling."""

    def test_result_contains_statistics(self, tmp_unorganised_dir):
        """Test that result contains expected statistics."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert result.files_processed > 0
        assert result.files_moved >= 0
        assert result.files_failed >= 0
        assert isinstance(result.categories_created, set)

    def test_result_includes_duration(self, tmp_unorganised_dir):
        """Test that result includes operation duration."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert result.duration_seconds >= 0

    def test_result_includes_errors(self, tmp_path):
        """Test that result includes error information."""
        # Create a file that can't be moved
        (tmp_path / "file.txt").write_text("content")

        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            directory=tmp_path,
            reporter=reporter,
            validate_paths=False,
        )

        result: OrganiserResult = organiser.organise_files(dry_run=True)

        assert isinstance(result.errors, list)
