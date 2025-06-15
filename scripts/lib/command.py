# -*- coding: utf-8 -*-
from __future__ import annotations
import subprocess
from typing import Any, Union

from recipes_convertor.logger import logger


class CommandResult:
    """Result of a command."""

    _original_command: list[str] | str
    _constructed_command: list[str] | str
    _command_prefix: list[str] | None
    _command_suffix: list[str] | None
    _executed_command: list[str] | str
    _used_shell: bool
    _captured_output: bool
    _returncode: int | None
    _error: str | Exception | None
    _stdout: str | None
    _stderr: str | None

    def __init__(
        self,
        original_command: list[str] | str,
        constructed_command: list[str] | str,
        command_prefix: list[str] | None,
        command_suffix: list[str] | None,
        executed_command: list[str] | str,
        used_shell: bool,
        captured_output: bool,
        returncode: int | None,
        error: str | Exception | None,
        stdout: str | None,
        stderr: str | None,
    ):
        self._original_command = original_command
        self._constructed_command = constructed_command
        self._command_prefix = command_prefix
        self._command_suffix = command_suffix
        self._executed_command = executed_command
        self._used_shell = used_shell
        self._captured_output = captured_output
        self._returncode = returncode
        self._error = error
        self._stdout = stdout
        self._stderr = stderr

    def __repr__(self) -> str:
        # pylint: disable=line-too-long
        status = "succeeded" if self._returncode == 0 else "failed"
        return f"CommandResult(executed_command={self._executed_command}, status={status})"

    @property
    def original_command(self) -> list[str] | str:
        """Get the original command."""
        return self._original_command

    @original_command.setter
    def original_command(self, _: list[str] | str) -> None:
        """Prevent setting the original command."""
        raise AttributeError("Cannot set original_command - it is read-only")

    @property
    def constructed_command(self) -> list[str] | str:
        """Get the constructed command."""
        return self._constructed_command

    @property
    def command_prefix(self) -> list[str] | None:
        """Get the command prefix."""
        return self._command_prefix

    @property
    def command_suffix(self) -> list[str] | None:
        """Get the command suffix."""
        return self._command_suffix

    @property
    def executed_command(self) -> list[str] | str:
        """Get the executed command."""
        return self._executed_command

    @property
    def used_shell(self) -> bool:
        """Get whether the command was run in a shell."""
        return self._used_shell

    @used_shell.setter
    def used_shell(self, _: bool) -> None:
        """Prevent setting used_shell - it is read-only."""
        raise AttributeError("Cannot set used_shell - it is read-only")

    @property
    def captured_output(self) -> bool:
        """Get whether the output was captured."""
        return self._captured_output

    @property
    def returncode(self) -> int | None:
        """Get the return code of the command."""
        return self._returncode

    @returncode.setter
    def returncode(self, _: int | None) -> None:
        """Prevent setting returncode - it is read-only."""
        raise AttributeError("Cannot set returncode - it is read-only")

    @property
    def error(self) -> str | Exception | None:
        """Get any error that occurred during command execution."""
        return self._error

    @error.setter
    def error(self, _: str | Exception | None) -> None:
        """Prevent setting error - it is read-only."""
        raise AttributeError("Cannot set error - it is read-only")

    @property
    def stdout(self) -> str | None:
        """Get the standard output of the command."""
        return self._stdout

    @stdout.setter
    def stdout(self, _: str | None) -> None:
        """Prevent setting stdout - it is read-only."""
        raise AttributeError("Cannot set stdout - it is read-only")

    @property
    def stderr(self) -> str | None:
        """Get the standard error of the command."""
        return self._stderr

    @stderr.setter
    def stderr(self, _: str | None) -> None:
        """Prevent setting stderr - it is read-only."""
        raise AttributeError("Cannot set stderr - it is read-only")

    @property
    def combined_output(self) -> dict[str, str | None]:
        """Get the combined output of the command."""
        return {
            "stdout": self._stdout,
            "stderr": self._stderr,
        }

    @combined_output.setter
    def combined_output(self, _: dict[str, str | None]) -> None:
        """Prevent setting combined_output - it is read-only."""
        raise AttributeError("Cannot set combined_output - it is read-only")

    @classmethod
    def from_subprocess_result(
        cls,
        result: subprocess.CompletedProcess[bytes],
        original_command: list[str],
        constructed_command: list[str] | str,
        command_prefix: list[str] | None,
        command_suffix: list[str] | None,
        used_shell: bool,
        captured_output: bool,
    ) -> CommandResult:
        """
        Create a CommandResult from a subprocess.CompletedProcess.

        Args:
            result: The subprocess.CompletedProcess to create a CommandResult from.
            used_shell: Whether the command was run in a shell.
            captured_output: Whether the output was captured.
            original_command: The original command.
            command_prefix: The command prefix.
            command_suffix: The command suffix.
        Returns:
            A CommandResult.
        """
        return cls(
            original_command=original_command,
            constructed_command=constructed_command,
            command_prefix=command_prefix,
            command_suffix=command_suffix,
            executed_command=result.args,
            used_shell=used_shell,
            captured_output=captured_output,
            returncode=result.returncode,
            error=None,
            stdout=result.stdout.decode("utf-8") if result.stdout else None,
            stderr=result.stderr.decode("utf-8") if result.stderr else None,
        )


class Command:
    """A command to run."""

    _command: list[str]

    def __init__(
        self,
        command: Union[list[str], str],
    ):
        self._command = command if isinstance(command, list) else command.split(" ")

    @property
    def command(self) -> list[str]:
        """Get the command."""
        return self._command

    @command.setter
    def command(self, _: list[str]) -> None:
        """Prevent setting the command."""
        raise AttributeError("Cannot set command - it is read-only")

    def _execute(
        self,
        check: bool = False,
        capture_output: bool = True,
        use_shell: bool = True,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run the command."""

        constructed_command: Union[list[str], str] = [
            *(command_prefix or []),
            *self.command,
            *(command_suffix or []),
        ]

        if use_shell and isinstance(constructed_command, list):
            constructed_command = " ".join(constructed_command)

        result = None
        try:
            logger.debug(
                f"Running command: {constructed_command}",
                cmd=constructed_command,
                using_shell=use_shell,
                capturing_output=capture_output,
                throw_error_on_non_zero_return_code=check,
            )

            result = subprocess.run(
                constructed_command,
                shell=use_shell,
                check=check,
                capture_output=capture_output,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            raise e

        return {
            "result": result,
            "original_command": self.command,
            "constructed_command": constructed_command,
            "command_prefix": command_prefix,
            "command_suffix": command_suffix,
            "used_shell": use_shell,
            "captured_output": capture_output,
        }

    def run(
        self,
        *args,
        check: bool = True,
        capture_output: bool = True,
        use_shell: bool = True,
        command_prefix: list[str] | None = None,
        command_suffix: list[str] | None = None,
        **kwargs,
    ) -> CommandResult:
        """Run the command."""
        # Warn about args/kwargs that were passed in that we're not using
        if args or kwargs:
            logger.warning(
                "Unknown arguments were passed to run() - this method does not use them",
                args=args,
                kwargs=kwargs,
            )

        execution_result = self._execute(
            check=check,
            capture_output=capture_output,
            use_shell=use_shell,
            command_prefix=command_prefix,
            command_suffix=command_suffix,
        )

        return CommandResult.from_subprocess_result(**execution_result)
