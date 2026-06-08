"""Constants for the file organiser."""

from pathlib import Path

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
