"""Main CLI entry point"""

from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from file_organiser.core.models import OrganiserResult

from typer_extensions import ExtendedTyper

from ..core.organiser import FileOrganiser
from ..utils.logging import get_logger

app = ExtendedTyper(help="File Organiser CLI")

logger: Logger = get_logger(name=__name__)


@app.command(aliases=["org", "o"])
def organise(
    directory: Path = app.Argument(default=..., help="Directory to organise"),
    dry_run: bool = app.Option(
        default=False, help="Simulate organisation without making changes"
    ),
    exclude_patterns: list[str] = app.Option(
        default=None, help="Patterns to exclude from organisation"
    ),
    include_hidden: bool = app.Option(
        default=False, help="Include hidden files in organisation"
    ),
    validate_paths: bool = app.Option(
        default=False, help="Validate file paths before organisation"
    ),
) -> None:
    """Organise files in the specified directory into category folders."""
    organiser = FileOrganiser(
        directory=directory,
        include_hidden=include_hidden,
        validate_paths=validate_paths,
    )

    result: OrganiserResult = organiser.organise_files(
        dry_run=dry_run, exclude_patterns=exclude_patterns
    )

    app.echo(message=result)


@app.command(aliases=["un", "u"])
def undo() -> None:
    """Undo the last organisation run."""
    app.echo(message="Not implemented yet")


@app.command(aliases=["st", "s"])
def stats() -> None:
    """Display statistics about the last organisation run."""
    app.echo(message="Not implemented yet")


@app.command(aliases=["val", "v"])
def validate(
    path: Path = app.Argument(default=..., help="Path to validate"),
) -> None:
    """Validate a directory or file path."""
    # ...call PathValidator...
    app.echo(message="Not implemented yet")


@app.command(name="list", aliases=["ls", "l"])
def list_categories() -> None:
    """List all known file categories."""
    app.echo(message="Not implemented yet")


@app.command(aliases=["cfg", "c"])
def config() -> None:
    """Configure File Organiser CLI."""
    app.echo(message="Not implemented yet")


if __name__ == "__main__":
    app()
