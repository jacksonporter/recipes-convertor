#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from git import Repo
from git.exc import InvalidGitRepositoryError
from recipes_convertor.logger import logger


class ProjectRootNotFoundError(Exception):
    """Raised when neither a git repository nor pyproject.toml can be found."""


def get_project_root() -> Path:
    """
    Get the root directory of the project by first trying to find a git repository,
    and if that fails, looking for a pyproject.toml file by traversing up the
    directory tree.

    Returns:
        Path: The absolute path to the project root directory

    Raises:
        InvalidGitRepositoryError: If git repository is invalid
        ProjectRootNotFoundError: If neither git repository nor pyproject.toml
            found
    """
    # First try to find git repository
    try:
        repo = Repo(Path.cwd(), search_parent_directories=True)
        if repo.working_tree_dir is None:
            raise InvalidGitRepositoryError("No working tree directory found")
        return Path(repo.working_tree_dir)
    except InvalidGitRepositoryError as exc:
        logger.warning("No git repository found, searching for pyproject.toml")

        # Search for pyproject.toml by traversing up the directory tree
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:  # Stop at root directory
            if (current_dir / "pyproject.toml").exists():
                return current_dir
            current_dir = current_dir.parent

        # If we get here, neither git repo nor pyproject.toml was found
        logger.error("No git repository or pyproject.toml found")
        raise ProjectRootNotFoundError("No git repository or pyproject.toml found") from exc
