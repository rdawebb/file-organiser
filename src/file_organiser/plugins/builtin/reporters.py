"""Builtin reporter plugins."""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.table import Table

from file_organiser.core.models import FileInfo, MoveResult, OrganiserResult
from ..base import PluginMetadata, ReporterPlugin


class RichReporterPlugin(ReporterPlugin):
    """Rich console reporter plugin."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialises the RichReporterPlugin.

        Args:
            verbose (bool, optional): Show detailed information.
        """
        self.verbose = verbose
        self.console = Console()
        self.progress: Optional[Progress] = None
        self.task_id: Optional[int] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="rich_reporter",
            version="0.1.0",
            author="Rob Webb",
            description="Rich-based terminal UI",
        )

    def on_start(self, total_files: int) -> None:
        """Initialises the progress display.

        Args:
            total_files (int): Total number of files to process.
        """
        self.console.print(
            Panel("[bold blue]Starting file organisation...[/bold blue]")
        )

        self.progress = Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
        )

        self.progress.start()
        self.task_id = self.progress.add_task(
            "[cyan]Organising files...", total=total_files
        )

    def on_file_processing(self, file_info: FileInfo) -> None:
        """Updates progress for current file.

        Args:
            file_info (FileInfo): Information about the file being processed.
        """
        if self.progress and self.task_id is not None:
            if self.verbose:
                self.progress.update(
                    self.task_id,
                    description=f"[cyan]Processing: [bold]{file_info.path.name}[/bold]",
                )

    def on_file_processed(self, result: MoveResult) -> None:
        """Advances progress after file is processed.

        Args:
            result (MoveResult): Result of the file move operation.
        """
        if self.progress and self.task_id is not None:
            self.progress.advance(self.task_id)

    def on_complete(self, result: OrganiserResult) -> None:
        """Displays the final summary.

        Args:
            result (OrganiserResult): The final organiser result.
        """
        if self.progress:
            self.progress.stop()

        self._display_summary(result)

        if result.errors:
            self._display_errors(result.errors)

    def on_error(self, error: Exception, file_info: Optional[FileInfo] = None) -> None:
        """Displays an error message.

        Args:
            error (Exception): The error that occurred.
            file_info (Optional[FileInfo], optional): Information about the file being processed.
        """
        if file_info:
            self.console.print(
                f"[bold red]Error processing file {file_info.path}:[/bold red] {error}"
            )
        else:
            self.console.print(f"[bold red]Error:[/bold red] {error}")

    def _display_summary(self, result: OrganiserResult) -> None:
        """Displays a summary table of the organisation results.

        Args:
            result (OrganiserResult): The final organiser result.
        """
        table = Table.grid(padding=(0, 2))
        table.add_column(style="yellow", justify="right")
        table.add_column()

        table.add_row("Files processed:", str(result.files_processed))
        table.add_row("Files moved:", str(result.files_moved))

        if result.files_skipped > 0:
            table.add_row("Files skipped:", str(result.files_skipped))

        if result.unknown_files > 0:
            table.add_row("Unknown file types:", f"[dim]{result.unknown_files}[/dim]")

        if result.files_failed > 0:
            table.add_row(
                "Files failed:", f"[bold red]{result.files_failed}[/bold red]"
            )

        table.add_row("Categories created:", str(len(result.categories_created)))
        table.add_row("Duration:", f"{result.duration_seconds:.2f}s")

        if result.categories_created:
            categories_list = "\n".join(
                f" • {category}" for category in sorted(result.categories_created)
            )
            table.add_row("", "")
            table.add_row("Categories:", "")
            table.add_row("", categories_list)

        title = "Dry Run Complete" if result.dry_run else "Success!"
        colour = "yellow" if result.dry_run else "green"

        panel = Panel.fit(
            table, title=f"[bold {colour}]{title}[/bold {colour}]", border_style=colour
        )

        self.console.print(panel)

    def _display_errors(self, errors: list) -> None:
        """Display error details.

        Args:
            errors (list): List of errors encountered.
        """
        self.console.print("\n[bold red]Errors encountered:[/bold red]")

        for path, error in errors[:10]:
            self.console.print(f" [red]•[/red] {path.name}: {error}")

        if len(errors) > 10:
            self.console.print(f"\n[dim]...and {len(errors) - 10} more errors[/dim]")


class SilentReporterPlugin(ReporterPlugin):
    """Silent reporter plugin - no output."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="silent_reporter",
            version="0.1.0",
            author="Rob Webb",
            description="No output reporter for testing or silent operations",
        )


class JSONReporterPlugin(ReporterPlugin):
    """JSON reporter plugin - outputs for scripting."""

    def __init__(self, output_path: Optional[Path] = None) -> None:
        """Initialises the JSONReporterPlugin.

        Args:
            output_path (Optional[Path], optional): Path to output JSON file.
                If None, outputs to stdout.
        """
        self.output_path = output_path
        self.start_time: Optional[float] = None
        self.console = Console()

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="json_reporter",
            version="0.1.0",
            author="Rob Webb",
            description="JSON output reporter for programmatic consumption",
        )

    def on_start(self, total_files: int) -> None:
        """Records the start time.

        Args:
            total_files (int): Total number of files to process.
        """
        import time

        self.start_time = time.time()

    def on_complete(self, result: OrganiserResult) -> None:
        """Outputs JSON summary.

        Args:
            result (OrganiserResult): The final organiser result.
        """
        output = {
            "success": result.success,
            "statistics": {
                "files_processed": result.files_processed,
                "files_moved": result.files_moved,
                "files_failed": result.files_failed,
                "files_skipped": result.files_skipped,
                "unknown_files": result.unknown_files,
                "duration_seconds": result.duration_seconds,
            },
            "categories": sorted(result.categories_created),
            "errors": [
                {"file": str(path), "error": str(error)}
                for path, error in result.errors
            ],
            "dry_run": result.dry_run,
        }

        json_output = json.dumps(output, indent=4)

        if self.output_path:
            self.output_path.write_text(json_output)
        else:
            self.console.print(json_output)
