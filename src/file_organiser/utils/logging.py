"""Centralised logging configuration and utilities."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Literal, Optional, TextIO

from file_organiser import file_mover  # type: ignore


class ColouredFormatter(logging.Formatter):
    """Custom logging formatter with colour support."""

    COLOURS: dict[str, str] = {
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
        level: Literal[10] = logging.DEBUG
    else:
        level: Any | Literal[20] = getattr(logging, log_level.upper(), logging.INFO)

    rust_handler: logging.StreamHandler[TextIO] = logging.StreamHandler()
    rust_handler.setLevel(level)

    console_handler: logging.StreamHandler[TextIO | Any] = logging.StreamHandler(
        stream=sys.stderr
    )
    console_handler.setLevel(level)

    if coloured and sys.stderr.isatty():
        console_formatter = ColouredFormatter(fmt="[PYTHON] %(levelname)s: %(message)s")
        rust_formatter = ColouredFormatter(fmt="[RUST] %(levelname)s: %(message)s")
    else:
        console_formatter = logging.Formatter(fmt="[PYTHON] %(levelname)s: %(message)s")
        rust_formatter = logging.Formatter(fmt="[RUST] %(levelname)s: %(message)s")

    rust_handler.setFormatter(fmt=rust_formatter)
    console_handler.setFormatter(fmt=console_formatter)

    if log_file:
        file_handler = RotatingFileHandler(
            filename=log_file, maxBytes=1 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(level=logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(fmt=file_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler],
    )

    rust_logger = logging.getLogger("rust")
    rust_logger.addHandler(rust_handler)
    rust_logger.propagate = False

    file_mover.init_logging()

    logging.getLogger(name="urllib3").setLevel(level=logging.WARNING)
    logging.getLogger(name="requests").setLevel(level=logging.WARNING)


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
        self.operation_name: str = operation_name
        self.logger: logging.Logger = logger or logging.getLogger(name=__name__)
        self.start_time: float = -1.0

    def __enter__(self):
        """Logs the start of the operation."""
        import time

        self.start_time: float = time.time()
        self.logger.info(msg=f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Logs the end of the operation."""
        import time

        if self.start_time != -1.0:
            duration: float = time.time() - self.start_time
        else:
            duration = 0.0
            self.logger.warning(
                msg=f"Operation '{self.operation_name}' ended without a valid start time."
            )

        if exc_type is None:
            self.logger.info(msg=f"Completed: {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(
                msg=f"Failed: {self.operation_name} after {duration:.2f}s - {exc_value}"
            )

        return False  # Do not suppress exceptions


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieves a logger instance.

    Args:
        name (Optional[str], optional): Name of the logger. Defaults to root logger if None.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)
