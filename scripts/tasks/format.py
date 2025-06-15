#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import json
from typing import Any

from recipes_convertor.logger import logger
import click

from scripts.lib.audit.format import (
    AVAILABLE_FORMATTERS,
    AVAILABLE_FORMATTER_NAMES,
    FormatterOperation,
    Formatter,
)
from scripts.lib.project import get_project_root


@click.command()
@click.option(
    "--formatter",
    type=click.Choice([*AVAILABLE_FORMATTER_NAMES, "all"]),
    default="all",
)
@click.option(
    "--output",
    type=click.Path(writable=True),
    default="format-results.json",
)
@click.option(
    "--do-not-use-mise-exec",
    is_flag=True,
    default=False,
)
@click.argument("file_paths", type=click.Path(exists=True), nargs=-1)
def main(formatter: str, output: str, file_paths: list[str], do_not_use_mise_exec: bool) -> None:
    """Format the code for the given file paths."""
    formatters_to_use: list[type[Formatter]] = (
        [AVAILABLE_FORMATTERS[formatter]]
        if formatter != "all"
        else list(AVAILABLE_FORMATTERS.values())
    )

    file_paths_to_check: list[str | Path] = list(file_paths) if file_paths else [get_project_root()]
    results: dict[str, dict[str, dict[str, Any]]] = {}
    was_successful = True

    for formatter_type in formatters_to_use:
        logger.info(
            f"Checking {', '.join(str(path) for path in file_paths_to_check)}",
            formatter=formatter_type.name,
        )
        for result in formatter_type.perform_formatter_operation(
            operation=FormatterOperation.FORMAT,
            file_paths=file_paths_to_check,
            command_prefix=(["mise", "exec", "--"] if not do_not_use_mise_exec else None),
        ):
            abs_path = str(result.path.absolute())
            if abs_path not in results:
                results[abs_path] = {}
            results[abs_path][formatter_type.name] = result.serialize()
            if not result.valid and was_successful:
                was_successful = False

    with open(output, "w", encoding="utf-8") as f:
        logger.info(f"Writing results to {output}")
        json.dump(results, f, indent=4)

    if not was_successful:
        logger.error("Formatting check failed")
        raise click.ClickException(f"Formatting check failed, see {output}")

    logger.info("Formatting finished")


def init() -> None:
    """Initialize the format module."""
    if __name__ == "__main__":
        # pylint: disable=no-value-for-parameter
        main()


init()
