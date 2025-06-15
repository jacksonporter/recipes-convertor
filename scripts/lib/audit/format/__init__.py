# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import importlib
import inspect
import pkgutil
from typing import Any, Generator

from recipes_convertor.logger import logger


class PathType(Enum):
    """Type of path."""

    FILE = "file"
    DIRECTORY = "directory"


class FileFormatResult:
    """Result of a format operation."""

    _path: Path
    _path_type: PathType
    _valid: bool
    _formatter: Formatter
    _formatted: bool | None
    _output: dict[str, str | None] | None

    def __init__(
        self,
        file_path: Path,
        formatter: Formatter,
        valid: bool = True,
        formatted: bool | None = None,
        output: dict[str, str | None] | None = None,
    ):
        if not file_path or not isinstance(file_path, Path):
            raise ValueError("file_path must be a Path object")

        if not formatter or not (isinstance(formatter, type)):
            raise ValueError("formatter must be a Formatter object")

        if not isinstance(valid, bool):
            raise ValueError("valid must be a boolean")

        if not isinstance(formatted, bool) and formatted is not None:
            raise ValueError("formatted must be a boolean or None")

        self._path = file_path
        self._path_type = PathType.FILE if self._path.is_file() else PathType.DIRECTORY
        self._valid = valid
        self._formatter = formatter
        self._formatted = formatted
        self._output = output

    @property
    def path(self) -> Path:
        """Get the path."""
        return self._path

    @path.setter
    def path(self, _: Path) -> None:
        """Set the path."""
        raise AttributeError("path is read-only")

    @property
    def path_type(self) -> PathType:
        """Get the path type."""
        return self._path_type

    @path_type.setter
    def path_type(self, _: PathType) -> None:
        """Set the path type."""
        raise AttributeError("path_type is read-only")

    @property
    def valid(self) -> bool:
        """Get the validity of the format operation."""
        return self._valid

    @valid.setter
    def valid(self, _: bool) -> None:
        """Set the validity of the format operation."""
        raise AttributeError("valid is read-only")

    @property
    def formatter(self) -> Formatter:
        """Get the formatter."""
        return self._formatter

    @formatter.setter
    def formatter(self, _: Formatter) -> None:
        """Set the formatter."""
        raise AttributeError("formatter is read-only")

    @property
    def formatted(self) -> bool | None:
        """Get the formatted status."""
        return self._formatted

    @formatted.setter
    def formatted(self, _: bool | None) -> None:
        """Set the formatted status."""
        raise AttributeError("formatted is read-only")

    @property
    def output(self) -> dict[str, str | None] | None:
        """Get the output of the format operation."""
        return self._output

    @output.setter
    def output(self, _: dict[str, str | None] | None) -> None:
        """Set the output of the format operation."""
        raise AttributeError("output is read-only")

    @property
    def combined_output(self) -> dict[str, str | None] | None:
        """Get the combined output of the format operation."""
        return {
            "stdout": self._output.get("stdout"),
            "stderr": self._output.get("stderr"),
        }

    @combined_output.setter
    def combined_output(self, _: dict[str, str | None] | None) -> None:
        """Set the combined output of the format operation."""
        raise AttributeError("combined_output is read-only")

    def serialize(self) -> dict[str, Any]:
        """Serialize the result."""
        return {
            "path": str(self._path),
            "path_type": self._path_type.value,
            "valid": self._valid,
            "formatted": self._formatted,
            "output": self._output,
        }


class FormatterError(Exception):
    """Error raised when a formatter fails."""

    given_message: str
    exit_code: int | None

    def __init__(self, given_message: str, exit_code: int | None = None):
        self.exit_code = exit_code

        if exit_code:
            self.given_message = f"[Exit Code: {exit_code}] {given_message}"
            logger.error(self.given_message)
        else:
            self.given_message = given_message
            logger.error(given_message)

        super().__init__(self.given_message)


class FormatterOperation(Enum):
    """Operation to perform on a formatter."""

    CHECK = "check"
    FORMAT = "format"


class Formatter(ABC):
    """Base class for formatters."""

    name: str

    @classmethod
    @abstractmethod
    def is_supported_filetype(cls, file_path: Path | str) -> bool:
        """Check if the file is a supported filetype."""
        raise NotImplementedError("is_supported_filetype method not implemented")

    @classmethod
    @abstractmethod
    def check(
        cls,
        file_path: Path,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> FileFormatResult:
        """Check if the files are formatted correctly.

        Args:
            files: List of files or paths to check

        Returns:
            FormatResult: Result of the check operation

        Raises:
            FormatterError: If the formatter fails
        """
        raise NotImplementedError("check method not implemented")

    @classmethod
    @abstractmethod
    def format(cls, file_path: Path) -> FileFormatResult:
        """Format the files.

        Args:
            files: List of files or paths to format

        Returns:
            FormatResult: Result of the format operation

        Raises:
            FormatterError: If the formatter fails
        """
        raise NotImplementedError("format method not implemented")

    @classmethod
    def perform_formatter_operation(
        cls,
        operation: FormatterOperation = FormatterOperation.CHECK,
        file_paths: list[Path] | list[str] | list[Path | str] | Path | str = Path("."),
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> Generator[FileFormatResult, None, None]:
        """Perform a formatter operation on the files."""
        logger.debug(f"Performing {operation.value} operation on {file_paths}")

        resolved_file_paths = None

        if not isinstance(file_paths, list):
            resolved_file_paths = [Path(file_paths)]
        else:
            resolved_file_paths = [
                Path(file_path) for file_path in file_paths if isinstance(file_path, (Path, str))
            ]

        try:
            operation_method = getattr(cls, operation.value)
        except AttributeError:
            error_msg = f"Invalid operation for formatter {cls.name}: {operation}"
            logger.error(error_msg)
            # pylint: disable=raise-missing-from
            raise FormatterError(error_msg, None)

        for file_path in resolved_file_paths:
            if not file_path.exists():
                error_msg = f"File does not exist: {file_path}"
                logger.error(error_msg)
                raise FormatterError(error_msg)
            if not cls.is_supported_filetype(file_path):
                warning_msg = f"File is not a supported filetype: {file_path}"
                logger.warning(warning_msg)
                continue

            result: FileFormatResult = operation_method(
                file_path, command_prefix=command_prefix, command_suffix=command_suffix
            )
            yield result


def _discover_formatters() -> dict[str, type[Formatter]]:
    """Discover all formatters in the formatters package."""
    formatters = {}
    formatters_package = Path(__file__).parent / "formatters"

    # Import all modules in the formatters directory
    for _, name, is_pkg in pkgutil.iter_modules([str(formatters_package)]):
        if not is_pkg:
            module = importlib.import_module(f".formatters.{name}", package=__package__)

            # Find all classes in the module that inherit from Formatter
            for _, item in inspect.getmembers(module):
                if inspect.isclass(item) and issubclass(item, Formatter) and item != Formatter:
                    if not hasattr(item, "name"):
                        raise FormatterError(
                            f"Formatter class {item.__name__} must define a 'name' class attribute"
                        )
                    if item.name.lower() == "all":
                        raise FormatterError(
                            f"Formatter class {item.__name__} cannot use 'all' as its name - "
                            "this is a reserved keyword"
                        )
                    if not item.name.isalnum() or not item.name.islower():
                        raise FormatterError(
                            f"Formatter class {item.__name__} must have a name that contains only "
                            "lowercase letters (a-z) and numbers (0-9)"
                        )
                    formatters[item.name] = item
                    logger.debug(f"Discovered formatter: {item.name} -> {item.__name__}")

    return formatters


AVAILABLE_FORMATTERS = _discover_formatters()
AVAILABLE_FORMATTER_NAMES = list(AVAILABLE_FORMATTERS.keys())
