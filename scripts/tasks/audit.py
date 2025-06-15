#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import json
from typing import Any

from recipes_convertor.logger import logger
import click

from scripts.lib.audit import (
    AVAILABLE_AUDITORS,
    AVAILABLE_AUDITOR_NAMES,
    AuditorOperation,
    Auditor,
)
from scripts.lib.project import get_project_root


@click.command()
@click.option(
    "--auditor",
    type=click.Choice([*AVAILABLE_AUDITOR_NAMES, "all"]),
    default="all",
)
@click.option(
    "--output",
    type=click.Path(writable=True),
    default="audit-results.json",
)
@click.option(
    "--do-not-use-mise-exec",
    is_flag=True,
    default=False,
)
@click.argument("file_paths", type=click.Path(exists=True), nargs=-1)
def main(auditor: str, output: str, file_paths: list[str], do_not_use_mise_exec: bool) -> None:
    """Format the code for the given file paths."""
    auditors_to_use: list[type[Auditor]] = (
        [AVAILABLE_AUDITORS[auditor]] if auditor != "all" else list(AVAILABLE_AUDITORS.values())
    )

    file_paths_to_check: list[str | Path] = list(file_paths) if file_paths else [get_project_root()]
    results: dict[str, dict[str, dict[str, Any]]] = {}
    was_successful = True

    for auditor_type in auditors_to_use:
        logger.info(
            f"Checking {', '.join(str(path) for path in file_paths_to_check)}",
            auditor=auditor_type.name,
        )
        for result in auditor_type.perform_auditor_operation(
            operation=AuditorOperation.AUDIT,
            file_paths=file_paths_to_check,
            command_prefix=(["mise", "exec", "--"] if not do_not_use_mise_exec else None),
        ):
            abs_path = str(result.path.absolute())
            if abs_path not in results:
                results[abs_path] = {}
            results[abs_path][auditor_type.name] = result.serialize()
            if not result.valid and was_successful:
                was_successful = False

    with open(output, "w", encoding="utf-8") as f:
        logger.info(f"Writing results to {output}")
        json.dump(results, f, indent=4)

    if not was_successful:
        logger.error("Audit check failed")
        raise click.ClickException(f"Audit check failed, see {output}")

    logger.info("Audit finished")


def init() -> None:
    """Initialize the format module."""
    if __name__ == "__main__":
        # pylint: disable=no-value-for-parameter
        main()


init()
