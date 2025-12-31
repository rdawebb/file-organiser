"""
Test suite for file_organiser core functionality.
Covers categoriser, models, mover, organiser, and validators modules.
"""

from pathlib import Path
import pytest

from file_organiser.core.categoriser import FileCategoriser
from file_organiser.core.models import (
    FileInfo,
    MoveResult,
    MoveStatus,
    OrganiserStats,
    OrganiserResult,
)
from file_organiser.core.mover import FileMover, MoveOptions
from file_organiser.core.organiser import FileOrganiser
from file_organiser.core.validators import PathValidator


# --- Categoriser Tests ---
def test_file_categoriser_fallback(monkeypatch):
    categoriser = FileCategoriser(plugin_registry=None, fallback_category="Other")
    dummy_file = FileInfo(
        path=Path("dummy.txt"),
        name="dummy.txt",
        extension=".txt",
        size=10,
        modified_time=0,
    )
    # No plugins, should fallback
    assert categoriser.categorise(dummy_file) == "Other"


def test_file_categoriser_batch():
    categoriser = FileCategoriser()
    files = [
        FileInfo(
            path=Path(f"file{i}.txt"),
            name=f"file{i}.txt",
            extension=".txt",
            size=1,
            modified_time=0,
        )
        for i in range(3)
    ]
    result = categoriser.categorise_batch(files)
    assert isinstance(result, dict)
    assert len(result) == 3


def test_file_categoriser_get_all_categories():
    categoriser = FileCategoriser()
    cats = categoriser.get_all_categories()
    assert "Uncategorised" in cats


# --- Models Tests ---
def test_move_result_success_and_failed():
    src = Path("a.txt")
    dst = Path("b.txt")
    mr_success = MoveResult(status=MoveStatus.SUCCESS, source=src, destination=dst)
    mr_failed = MoveResult(
        status=MoveStatus.FAILED, source=src, destination=None, error=Exception("fail")
    )
    assert mr_success.success
    assert not mr_failed.success
    assert mr_failed.failed


def test_organiser_stats_record_result():
    stats = OrganiserStats()
    src = Path("a.txt")
    dst = Path("b.txt")
    mr = MoveResult(
        status=MoveStatus.SUCCESS, source=src, destination=dst, category="testcat"
    )
    stats.record_result(mr)
    assert stats.files_processed == 1
    assert stats.files_moved == 1
    assert "testcat" in stats.categories_used


# --- Mover Tests ---
def test_file_mover_move_file(tmp_path):
    src = tmp_path / "source.txt"
    dst_dir = tmp_path / "dest"
    src.write_text("hello")
    mover = FileMover(MoveOptions())
    result = mover.move_file(src, dst_dir)
    assert result.status == MoveStatus.SUCCESS
    assert result.destination.exists()
    assert not src.exists()


def test_file_mover_dry_run(tmp_path):
    src = tmp_path / "source.txt"
    dst_dir = tmp_path / "dest"
    src.write_text("hello")
    mover = FileMover(MoveOptions())
    result = mover.move_file(src, dst_dir, dry_run=True)
    assert result.status == MoveStatus.DRY_RUN
    assert src.exists()
    assert not (dst_dir / "source.txt").exists()


# --- Organiser Tests ---
class DummyReporter:
    def on_start(self, total_files=None):
        pass

    def on_file_processing(self, file_info):
        pass

    def on_file_processed(self, result):
        pass

    def on_complete(self, result):
        pass


def test_file_organiser_organise_files(tmp_path):
    # Create files
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    organiser = FileOrganiser(
        tmp_path, include_hidden=False, validate_paths=True, reporter=DummyReporter()
    )
    result = organiser.organise_files(dry_run=True)
    assert isinstance(result, OrganiserResult)
    assert result.files_processed >= 2


# --- Validators Tests ---
def test_path_validator_valid(tmp_path):
    PathValidator.validate_directory(tmp_path)
    # Should not raise


def test_path_validator_invalid():
    with pytest.raises(FileNotFoundError):
        PathValidator.validate_directory(Path("/not/a/real/dir/hopefully"))
    # validate_category_name is a classmethod, so call with class as first arg
    with pytest.raises(ValueError):
        PathValidator.validate_category_name("bad/name")
    with pytest.raises(ValueError):
        PathValidator.validate_category_name("..")
    with pytest.raises(ValueError):
        PathValidator.validate_category_name("/abs")
