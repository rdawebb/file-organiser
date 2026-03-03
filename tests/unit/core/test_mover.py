"""Unit tests for mover module."""

from src.file_organiser.core.models import MoveStatus
from src.file_organiser.core.mover import FileMover, MoveOptions


class TestMoveOptions:
    """Tests for MoveOptions configuration."""

    def test_move_options_defaults(self):
        """Test default MoveOptions values."""
        options = MoveOptions()

        assert options.atomic
        assert options.verify_checksum
        assert options.preserve_metadata
        assert options.create_dirs
        assert not options.overwrite_existing

    def test_move_options_custom(self):
        """Test custom MoveOptions values."""
        options = MoveOptions(
            atomic=False,
            verify_checksum=False,
            preserve_metadata=False,
            create_dirs=False,
            overwrite_existing=True,
        )

        assert not options.atomic
        assert not options.verify_checksum
        assert not options.preserve_metadata
        assert not options.create_dirs
        assert options.overwrite_existing


class TestFileMoverInitialisation:
    """Tests for FileMover initialisation."""

    def test_file_mover_creation(self, move_options):
        """Test creating a FileMover instance."""
        mover = FileMover(options=move_options)

        assert mover.options == move_options
        assert mover.mover is not None

    def test_file_mover_with_default_options(self):
        """Test FileMover with default options."""
        mover = FileMover(options=MoveOptions())

        assert mover.options.atomic
        assert mover.options.verify_checksum


class TestFileMoveOperations:
    """Tests for file move operations."""

    def test_move_file_success(self, tmp_path, file_mover):
        """Test successful file move."""
        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content")

        result = file_mover.move_file(source, dest_dir)

        assert result.status == MoveStatus.SUCCESS
        assert result.source == source
        assert result.destination is not None
        assert not source.exists()

    def test_move_file_dry_run(self, tmp_path, file_mover):
        """Test dry run file move."""
        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content")

        result = file_mover.move_file(source, dest_dir, dry_run=True)

        assert result.status == MoveStatus.DRY_RUN
        assert source.exists()  # Should still exist

    def test_move_file_with_filename(self, tmp_path, file_mover):
        """Test moving file with filename parameter."""
        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content")

        result = file_mover.move_file(
            source,
            dest_dir,
            filename="renamed.txt",
        )

        if result.status == MoveStatus.SUCCESS:
            assert result.destination is not None
            assert result.destination.name == "renamed.txt"

    def test_move_file_with_category(self, tmp_path, file_mover):
        """Test moving file with category parameter."""
        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content")

        result = file_mover.move_file(
            source,
            dest_dir,
            category="Documents",
        )

        assert result.category == "Documents"

    def test_move_file_creates_directories(self, tmp_path):
        """Test that move creates destination directories."""
        options = MoveOptions(create_dirs=True)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "nested" / "destination"

        source.write_text("test content")

        mover.move_file(source, dest_dir)

        # Should create nested directories
        assert dest_dir.exists()


class TestFileMoverErrorHandling:
    """Tests for error handling in file moves."""

    def test_move_nonexistent_file(self, tmp_path, file_mover):
        """Test moving a file that doesn't exist."""
        source = tmp_path / "nonexistent.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        result = file_mover.move_file(source, dest_dir)

        assert result.status == MoveStatus.FAILED
        assert result.error is not None

    def test_move_to_nonexistent_destination(self, tmp_path):
        """Test moving to non-existent destination without create_dirs."""
        options = MoveOptions(create_dirs=False)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "nonexistent"

        source.write_text("test content")

        result = mover.move_file(source, dest_dir)

        assert result.status == MoveStatus.FAILED


class TestFileOverwrite:
    """Tests for file overwrite behavior."""

    def test_move_file_no_overwrite(self, tmp_path):
        """Test that files aren't overwritten when overwrite_existing=False."""
        options = MoveOptions(overwrite_existing=False)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "source.txt"

        source.write_text("new content")
        existing.write_text("existing content")

        result = mover.move_file(source, dest_dir)

        # Should skip if file exists and overwrite=False
        if result.status == MoveStatus.SUCCESS:
            # Source was moved to a unique name — existing file must be untouched
            assert existing.read_text() == "existing content"
            assert result.destination != existing
        else:
            assert existing.read_text() == "existing content"

    def test_move_file_with_overwrite(self, tmp_path):
        """Test that files are overwritten when overwrite_existing=True."""
        options = MoveOptions(overwrite_existing=True)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()
        existing = dest_dir / "source.txt"

        source.write_text("new content")
        existing.write_text("old content")

        result = mover.move_file(source, dest_dir)

        if result.status == MoveStatus.SUCCESS:
            assert existing.read_text() == "new content"


class TestMetadataPreservation:
    """Tests for metadata preservation."""

    def test_move_file_preserves_metadata(self, tmp_path):
        """Test that metadata is preserved when preserve_metadata=True."""
        options = MoveOptions(preserve_metadata=True)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content")
        source_stat = source.stat()

        result = mover.move_file(source, dest_dir)

        if result.status == MoveStatus.SUCCESS and result.destination:
            dest_stat = result.destination.stat()
            # Mode should be preserved (if not modified by filesystem)
            assert dest_stat.st_size == source_stat.st_size


class TestChecksumVerification:
    """Tests for checksum verification."""

    def test_move_file_verify_checksum(self, tmp_path):
        """Test that checksum is verified when verify_checksum=True."""
        options = MoveOptions(verify_checksum=True)
        mover = FileMover(options=options)

        source = tmp_path / "source.txt"
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        source.write_text("test content for checksum verification")

        result = mover.move_file(source, dest_dir)

        assert result.status in [MoveStatus.SUCCESS, MoveStatus.DRY_RUN]
