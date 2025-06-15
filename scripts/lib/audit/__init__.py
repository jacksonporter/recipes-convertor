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


class FileAuditResult:
    """Result of a audit operation."""

    _path: Path
    _path_type: PathType
    _valid: bool
    _auditor: Auditor
    _output: dict[str, str | None] | None

    def __init__(
        self,
        file_path: Path,
        auditor: Auditor,
        valid: bool = True,
        output: dict[str, str | None] | None = None,
    ):
        if not file_path or not isinstance(file_path, Path):
            raise ValueError("file_path must be a Path object")

        if not auditor or not (isinstance(auditor, type)):
            raise ValueError("auditor must be a Auditor object")

        if not isinstance(valid, bool):
            raise ValueError("valid must be a boolean")

        self._path = file_path
        self._path_type = PathType.FILE if self._path.is_file() else PathType.DIRECTORY
        self._valid = valid
        self._auditor = auditor
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
    def auditor(self) -> Auditor:
        """Get the auditor."""
        return self._auditor

    @auditor.setter
    def auditor(self, _: Auditor) -> None:
        """Set the auditor."""
        raise AttributeError("auditor is read-only")

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
            "output": self._output,
        }


class AuditorError(Exception):
    """Error raised when a auditor fails."""

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


class AuditorOperation(Enum):
    """Operation to perform on a auditor."""

    AUDIT = "audit"


class Auditor(ABC):
    """Base class for auditors."""

    name: str

    @classmethod
    @abstractmethod
    def is_supported_filetype(cls, file_path: Path | str) -> bool:
        """Check if the file is a supported filetype."""
        raise NotImplementedError(
            "is_supported_filetype method not implemented"
        )  # pragma: no cover

    @classmethod
    @abstractmethod
    def audit(
        cls,
        file_path: Path,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> FileAuditResult:
        """Audit the files.

        Args:
            files: List of files or paths to check

        Returns:
            AuditResult: Result of the audit operation

        Raises:
            AuditorError: If the auditor fails
        """
        raise NotImplementedError("audit method not implemented")

    @classmethod
    def perform_auditor_operation(
        cls,
        operation: AuditorOperation = AuditorOperation.AUDIT,
        file_paths: list[Path] | list[str] | list[Path | str] | Path | str = Path("."),
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> Generator[FileAuditResult, None, None]:
        """Perform a auditor operation on the files."""
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
            error_msg = f"Invalid operation for auditor {cls.name}: {operation}"
            logger.error(error_msg)
            # pylint: disable=raise-missing-from
            raise AuditorError(error_msg, None)

        for file_path in resolved_file_paths:
            if not file_path.exists():
                error_msg = f"File does not exist: {file_path}"
                logger.error(error_msg)
                raise AuditorError(error_msg)
            if not cls.is_supported_filetype(file_path):
                warning_msg = f"File is not a supported filetype: {file_path}"
                logger.warning(warning_msg)
                continue

            result: FileAuditResult = operation_method(
                file_path, command_prefix=command_prefix, command_suffix=command_suffix
            )
            yield result


def _discover_auditors() -> dict[str, type[Auditor]]:
    """Discover all auditors in the auditors package."""
    auditors = {}
    auditors_package = Path(__file__).parent / "auditors"

    # Import all modules in the auditors directory
    for _, name, is_pkg in pkgutil.iter_modules([str(auditors_package)]):
        if not is_pkg:
            module = importlib.import_module(f".auditors.{name}", package=__package__)

            # Find all classes in the module that inherit from Auditor
            for _, item in inspect.getmembers(module):
                if inspect.isclass(item) and issubclass(item, Auditor) and item != Auditor:
                    if not hasattr(item, "name"):
                        raise AuditorError(
                            f"Auditor class {item.__name__} must define a 'name' class attribute"
                        )
                    if item.name.lower() == "all":
                        raise AuditorError(
                            f"Auditor class {item.__name__} cannot use 'all' as its name - "
                            "this is a reserved keyword"
                        )
                    if not item.name.isalnum() or not item.name.islower():
                        raise AuditorError(
                            f"Auditor class {item.__name__} must have a name that contains only "
                            "lowercase letters (a-z) and numbers (0-9)"
                        )
                    auditors[item.name] = item
                    logger.debug(f"Discovered auditor: {item.name} -> {item.__name__}")

    return auditors


AVAILABLE_AUDITORS = _discover_auditors()
AVAILABLE_AUDITOR_NAMES = list(AVAILABLE_AUDITORS.keys())
