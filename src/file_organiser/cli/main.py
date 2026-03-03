"""Main CLI entry point"""

from pathlib import Path

from typer_extensions import ExtendedTyper

from src.file_organiser.core.organiser import FileOrganiser
from src.file_organiser.utils.logging import get_logger

app = ExtendedTyper(help="File Organiser CLI")

logger = get_logger(__name__)


def organise(
    directory: Path = app.Argument(..., help="Directory to organise"),
    dry_run: bool = app.Option(
        False, help="Simulate organisation without making changes"
    ),
    exclude_patterns: list[str] = app.Option(
        None, help="Patterns to exclude from organisation"
    ),
    include_hidden: bool = app.Option(
        False, help="Include hidden files in organisation"
    ),
    validate_paths: bool = app.Option(
        False, help="Validate file paths before organisation"
    ),
) -> None:
    """Organise files in the specified directory into category folders."""
    organiser = FileOrganiser(
        directory=directory,
        include_hidden=include_hidden,
        validate_paths=validate_paths,
    )

    result = organiser.organise_files(
        dry_run=dry_run, exclude_patterns=exclude_patterns
    )

    app.echo(result)


def undo() -> None:
    """Undo the last organisation run."""
    app.echo("Not implemented yet")


def stats() -> None:
    """Display statistics about the last organisation run."""
    app.echo("Not implemented yet")


def validate(
    path: Path = app.Argument(..., help="Path to validate"),
) -> None:
    """Validate a directory or file path."""
    # ...call PathValidator...
    app.echo("Not implemented yet")


def list_categories() -> None:
    """List all known file categories."""
    app.echo("Not implemented yet")


def config() -> None:
    """Configure File Organiser CLI."""
    app.echo("Not implemented yet")


# Command Aliases
app.add_aliased_command(organise, "organise", ["org", "o"])
app.add_aliased_command(undo, "undo", ["un", "u"])
app.add_aliased_command(stats, "stats", ["st", "s"])
app.add_aliased_command(validate, "validate", ["val", "v"])
app.add_aliased_command(list_categories, "list", ["ls", "l"])
app.add_aliased_command(config, "config", ["cfg", "c"])


if __name__ == "__main__":
    app()
