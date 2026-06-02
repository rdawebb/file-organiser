"""Constants for the file organiser."""

from pathlib import Path

EXTENSIONS_PATH: Path = (
    Path(__file__).parent.parent.parent / "data" / "default_extensions.py"
)

FALLBACK_CATEGORY = "Unknown"

FORBIDDEN_PATHS: set[Path] = {
    Path("/"),
    Path("/etc"),
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/boot"),
    Path("/sys"),
    Path("/proc"),
    Path("/dev"),
    Path("/var"),
    Path("/tmp"),
    Path("/System"),  # macOS system folder
}
