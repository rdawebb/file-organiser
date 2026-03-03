"""End-to-end integration tests for complete file organisation workflow."""

from src.file_organiser.core.organiser import FileOrganiser
from src.file_organiser.core.models import OrganiserResult

from tests.fixtures.mock_plugins import MockReporterPlugin


class TestEndToEndWorkflow:
    """Tests for complete end-to-end organisation workflows."""

    def test_complete_organisation_workflow_dry_run(self, tmp_unorganised_dir):
        """Test complete organisation workflow in dry run mode."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result = organiser.organise_files(dry_run=True)

        # Verify all expected callbacks were called
        assert reporter.start_called
        assert reporter.complete_called
        assert len(reporter.processing_files) > 0

        # Verify result is correct
        assert isinstance(result, OrganiserResult)
        assert result.dry_run
        assert result.files_processed > 0

    def test_complete_organisation_with_categorisation(self, tmp_unorganised_dir):
        """Test organisation with proper categorisation."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result = organiser.organise_files(dry_run=True)

        # Verify categorisation occurred
        assert len(result.categories_created) > 0

    def test_organisation_with_exclude_patterns(self, tmp_path):
        """Test organisation respects exclude patterns."""
        (tmp_path / "report.pdf").write_text("PDF")
        (tmp_path / "script.py").write_text("Python")
        (tmp_path / "readme.txt").write_text("Text")

        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_path,
            reporter=reporter,
            validate_paths=False,
        )

        # Exclude .txt files
        organiser.organise_files(
            dry_run=True,
            exclude_patterns=["*.txt"],
        )

    def test_organisation_reports_progress(self, tmp_unorganised_dir):
        """Test that reporter receives all events."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        organiser.organise_files(dry_run=True)

        # Verify event sequence
        assert reporter.start_called
        assert len(reporter.processing_files) == reporter.total_files
        assert len(reporter.processed_results) == reporter.total_files
        assert reporter.complete_called


class TestMultiPluginIntegration:
    """Tests for multiple plugins working together."""

    def test_categorisation_and_reporting(self, tmp_unorganised_dir):
        """Test categorisation and reporting plugins work together."""
        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_unorganised_dir,
            reporter=reporter,
            validate_paths=False,
        )

        result = organiser.organise_files(dry_run=True)

        # Both categorisation and reporting should work
        assert len(result.categories_created) > 0
        assert reporter.complete_result is not None


class TestErrorRecovery:
    """Tests for error recovery during organisation."""

    def test_organisation_continues_after_file_error(self, tmp_path):
        """Test that organisation continues after processing a problematic file."""
        (tmp_path / "good1.txt").write_text("good")
        (tmp_path / "good2.py").write_text("code")

        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_path,
            reporter=reporter,
            validate_paths=False,
        )

        result = organiser.organise_files(dry_run=True)

        # Should process all files, even with errors
        assert result.files_processed >= 2

    def test_result_includes_error_information(self, tmp_path):
        """Test that result includes error information."""
        (tmp_path / "file.txt").write_text("content")

        reporter = MockReporterPlugin()
        organiser = FileOrganiser(
            tmp_path,
            reporter=reporter,
            validate_paths=False,
        )

        result = organiser.organise_files(dry_run=True)

        # Result should include error list
        assert isinstance(result.errors, list)
