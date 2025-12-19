"""Centralised logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from typing import Optional


class ColouredFormatter(logging.Formatter):
    """Custom logging formatter with colour support."""

    COLOURS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record) -> str:
        """Formats the log record with colours based on severity level."""
        if record.levelname in self.COLOURS:
            record.levelname = (
                f"{self.COLOURS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    verbose: bool = False,
    coloured: bool = True,
) -> None:
    """Sets up logging configuration.

    Args:
        log_file (Optional[Path], optional): Path to log file. Logs to console if None. Defaults to None.
        level (str, optional): Logging level. Defaults to "INFO".
        verbose (bool, optional): If True, sets level to DEBUG. Defaults to False.
        coloured (bool, optional): If True, uses coloured output for console logs. Defaults to True.
    """
    if verbose:
        level = logging.DEBUG
    else:
        level = getattr(logging, log_level.upper(), logging.INFO)

    handlers = []

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    if coloured and sys.stderr.isatty():
        console_formatter = ColouredFormatter("%(levelname)s: %(message)s")
    else:
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


class OperationLogger:
    """Context manager for logging the start and end of an operation."""

    def __init__(
        self, operation_name: str, logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialises the OperationLogger.

        Args:
            operation_name (str): The name of the operation.
            logger (Optional[logging.Logger], optional): Logger instance to use. Defaults to root logger.
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None

    def __enter__(self):
        """Logs the start of the operation."""
        import time

        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Logs the end of the operation."""
        import time

        duration = time.time() - self.start_time

        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(
                f"Failed: {self.operation_name} after {duration:.2f}s - {exc_value}"
            )

        return False  # Do not suppress exceptions
