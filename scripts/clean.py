"""Cache cleaning script"""

from pathlib import Path
import shutil

CACHE_DIRS = ["__pycache__", "*.egg-info", ".pytest_cache", "ruff_cache"]


def clean_cache(root_dir=Path(".")):
    """Remove cache files"""
    for path in Path(root_dir).rglob("*"):
        if path.is_dir() and path.name in CACHE_DIRS:
            shutil.rmtree(path, ignore_errors=True)
    print("Cache cleaned!")


if __name__ == "__main__":
    clean_cache()
