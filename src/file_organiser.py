"""File organiser module to categorise files based on their MIME types."""

from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from extensions import EXTENSIONS


class FileOrganiser:
    """A class to organise files in a directory into subdirectories based file type"""

    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)

    def _check_collision(self, category_folder: Path, filename: str) -> str:
        """
        Checks for filename collisions in the target directory and modifies the filename if necessary

        Args:
            category_folder (Path): The target directory where the file will be moved
            filename (str): The original filename
        
        Returns:
            str: A unique filename to avoid collisions
        """
        if any(entry.name == filename for entry in category_folder.iterdir()):
            base = Path(filename).stem
            extension = Path(filename).suffix
            count = 1
            while True:
                new_filename = f"{base}({count}){extension}"
                new_dest_path = category_folder / new_filename
                if not new_dest_path.exists():
                    return new_filename
                count += 1
        return filename
    
    def _process_file(
        self,
        dirpath: Path,
        filename: str,
        category: str,
        folders_created: set[Path],
        dry_run: bool,
        console: Console
    ) -> str:
        """
        Processes a single file: checks for collisions, moves the file, and updates tracking variables

        Args:
            dirpath (Path): The directory path of the file
            filename (str): The name of the file
            category_folder (Path): The target category folder
            folders_created (set[Path]): Set of created folders
            dry_run (bool): If True, does not actually move files
            console (Console): Rich console for logging

        Returns:
            str: 'success' or 'error' based on the operation result
        """
        category_folder = Path(self.directory) / category
        folders_created.add(category_folder)
        source_path = Path(dirpath) / filename
        unique_filename = self._check_collision(category_folder, filename)
        dest_path = category_folder / unique_filename

        if dry_run:
            return 'success'
        else:
            category_folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(source_path, dest_path)
                return 'success'
            except Exception as e:
                console.print(f"[bold red]Error moving file {filename}:[/bold red] {e}")
                return 'error'

    def organise_files(self, dry_run: bool) -> None:
        """
        Organises files in the specified directory into subdirectories based on their file types

        Args:
            dry_run (bool): If True, simulates the organisation without moving files
        """
        console = Console()
        console.print("[bold blue]Starting file organisation...[/bold blue]")
        files_moved: int = 0
        unknown_files: int = 0
        folders_created: set[Path] = set()
        file_count: int = sum(1 for _ in self.directory.rglob('*') if _.is_file())
        with Progress() as progress:
            task = progress.add_task("[cyan]Organising files...", total=file_count)
            for file_path in self.directory.rglob('*'):
                if file_path.is_file():
                    dirpath = file_path.parent
                    filename = file_path.name
                    ext = Path(filename).suffix.lower()

                    if ext in EXTENSIONS:
                        category = EXTENSIONS[ext]
                        result = self._process_file(
                            dirpath,
                            filename,
                            category,
                            folders_created,
                            dry_run,
                            console
                        )
                        if result == 'success':
                            files_moved += 1
                    else:
                        file_path = Path(dirpath) / filename
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if mime_type:
                            main_type = mime_type.split('/')[0]
                            result = self._process_file(
                                dirpath,
                                filename,
                                main_type,
                                folders_created,
                                dry_run,
                                console
                            )
                            if result == 'success':
                                files_moved += 1
                        else:
                            result = self._process_file(
                                dirpath,
                                filename,
                                'unknown',
                                folders_created,
                                dry_run,
                                console
                            )
                            if result == 'success':
                                unknown_files += 1
                    progress.advance(task)

        if dry_run:
            dry_run_panel = Panel.fit(
                f"[bold yellow]Dry run complete! No files were moved[/bold yellow]\n\n"
                f"[bold yellow]Files that would be moved:[/bold yellow] {files_moved}\n"
                f"[bold yellow]Files of unknown type that would be moved:[/bold yellow] {unknown_files}\n"
                f"[bold yellow]Folders that would be created:[/bold yellow] {len(folders_created)}\n" +
                "\n".join(f" - {folder}" for folder in folders_created),
                title="Dry Run"
            )
            console.print(dry_run_panel)
        else:
            summary_panel = Panel.fit(
                f"[bold green]File organisation complete![/bold green]\n\n"
                f"[bold yellow]Files moved:[/bold yellow] {files_moved}\n"
                f"[bold yellow]Files of unknown type moved:[/bold yellow] {unknown_files}\n"
                f"[bold yellow]Folders created:[/bold yellow] {len(folders_created)}\n" +
                "\n".join(f" - {folder}" for folder in folders_created),
                title="Success"
            )
            console.print(summary_panel)