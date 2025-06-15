#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from recipes_convertor.logger import logger

from scripts.lib.command import Command
from scripts.lib.audit.format import Formatter, FormatterError, FileFormatResult


class BlackFormatter(Formatter):
    """Formatter for black."""

    name = "black"
    executable = "black"

    def __init__(self):
        super().__init__(self.name)

    @classmethod
    def is_supported_filetype(cls, file_path: Path | str) -> bool:
        """Check if the file is a supported filetype."""
        if not isinstance(file_path, Path):
            raise TypeError(f"file_path must be a Path, got {type(file_path)}")

        if file_path.is_dir():
            return True

        return "py" in file_path.suffix.lower()

    @classmethod
    def check(
        cls,
        file_path: Path,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> FileFormatResult:
        """Check if the files are formatted correctly."""
        logger.debug(f"Running black check on {file_path}")
        command = Command([cls.executable, "--check"])

        result = command.run(
            check=False,
            command_prefix=command_prefix,
            command_suffix=[*[str(file_path)], *(command_suffix or [])],
        )
        valid = result.returncode == 0
        match result.returncode:
            case 0:
                valid = True
                logger.debug(f"{file_path} is properly formatted")
            case 1:
                valid = False
                logger.debug(f"{file_path} needs formatting")
            case _:
                error_msg = f"Unknown error: {result.returncode}"
                logger.error(error_msg)
                raise FormatterError(error_msg, result.returncode)

        return FileFormatResult(
            file_path=file_path,
            formatter=cls,
            valid=valid,
            formatted=None,
            output=result.combined_output if result else None,
        )

    @classmethod
    def format(
        cls,
        file_path: Path,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> FileFormatResult:
        """Format the file and return whether changes were made."""
        logger.debug(f"Checking if {file_path} needs formatting")
        # First check if changes are needed
        check_result = cls.check(
            file_path, command_prefix=command_prefix, command_suffix=command_suffix
        )
        needs_changes = not check_result.valid

        result = None
        if needs_changes:
            logger.info(f"Formatting {file_path}")
            # Only run the formatter if changes are needed
            command = Command([cls.executable])
            result = command.run(
                check=False,
                command_prefix=command_prefix,
                command_suffix=[*[str(file_path)], *(command_suffix or [])],
            )
            if result.returncode != 0:
                error_msg = f"Failed to format file: {file_path}"
                logger.error(error_msg)
                raise FormatterError(error_msg, result.returncode)
            logger.info(f"Successfully formatted {file_path}")
        else:
            logger.debug(f"{file_path} is already properly formatted")

        return FileFormatResult(
            file_path=file_path,
            formatter=cls,
            valid=True,
            formatted=needs_changes,
            output=result.combined_output if result else None,
        )
