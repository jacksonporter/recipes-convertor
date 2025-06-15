#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from recipes_convertor.logger import logger

from scripts.lib.command import Command
from scripts.lib.audit import Auditor, AuditorError, FileAuditResult


class FlakeEightAuditor(Auditor):
    """Auditor for flake8."""

    name = "flake8"
    executable = ["flake8"]

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
    def audit(
        cls,
        file_path: Path,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> FileAuditResult:
        """Audit the files."""
        logger.debug(f"Running flake8 audit on {file_path}")
        command = Command(cls.executable)

        result = command.run(
            check=False,
            command_prefix=command_prefix,
            command_suffix=[*[str(file_path)], *(command_suffix or [])],
        )
        valid = result.returncode == 0
        match result.returncode:
            case 0:
                valid = True
                logger.debug(f"{file_path} is properly audited")
            case 1:
                valid = False
                logger.debug(f"{file_path} needs auditing")
            case _:
                error_msg = f"Unknown error: {result.returncode}"
                logger.error(error_msg)
                raise AuditorError(error_msg, result.returncode)

        return FileAuditResult(
            file_path=file_path,
            auditor=cls,
            valid=valid,
            output=result.combined_output if result else None,
        )
