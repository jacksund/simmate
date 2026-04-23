# -*- coding: utf-8 -*-

"""
This defines commands for Simmate development tasks. All commands are
accessible through the `simmate dev` command.
"""

import logging
import shutil
import subprocess
from pathlib import Path

import typer

dev_app = typer.Typer(rich_markup_mode="markdown")


@dev_app.callback(no_args_is_help=True)
def dev():
    """
    Commands for Simmate development (linting, testing, docs, and cleanup).
    """
    pass


@dev_app.command()
def lint():
    """
    Runs black, isort, and djlint to format and lint the codebase.
    """
    logging.info("Running black...")
    subprocess.run("black .", shell=True)

    logging.info("Running isort...")
    subprocess.run("isort .", shell=True)

    logging.info("Running djlint...")
    subprocess.run("djlint . --reformat", shell=True)


@dev_app.command()
def test(
    full: bool = typer.Option(
        False,
        "--full",
        help="Runs the full test suite, including VASP tests.",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Runs tests in parallel using pytest-xdist.",
    ),
):
    """
    Runs the test suite using pytest.
    """
    command = "pytest"
    if full:
        # As defined in maintainer_notes.md, full tests exclude blender but include vasp
        command += ' -m "not blender"'
    if parallel:
        command += " -n auto"

    logging.info(f"Running command: {command}")
    subprocess.run(command, shell=True)


@dev_app.command()
def docs():
    """
    Starts a local development server for the documentation.
    """
    logging.info("Starting mkdocs serve...")
    subprocess.run("mkdocs serve", shell=True)


@dev_app.command()
def clean():
    """
    Removes temporary files, build artifacts, and empty directories.
    """
    # 1. Remove common artifacts/cache folders and files
    patterns = [
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.coverage",
        "**/htmlcov",
        "**/dist",
        "**/build",
        "**/*.egg-info",
        "**/.djlint_cache",
    ]

    logging.info("Removing artifacts and cache files...")
    for pattern in patterns:
        for path in Path.cwd().glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as e:
                logging.warning(f"Failed to remove {path}: {e}")

    # 2. Remove empty directories
    logging.info("Removing empty directories...")
    # We walk bottom-up so that we can remove parent directories that become
    # empty after their children are removed.
    for path in sorted(Path.cwd().glob("**/"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            # Safety check: don't delete .git or .venv even if empty (unlikely)
            if ".git" not in path.parts and ".venv" not in path.parts:
                try:
                    path.rmdir()
                except Exception as e:
                    logging.warning(f"Failed to remove empty directory {path}: {e}")

    logging.info("Cleanup complete! :sparkles:")


@dev_app.command()
def prebuild():
    """
    Creates a date-stamped zip file of the current SQLite3 database.
    """
    from simmate.database.utils import create_prebuild

    create_prebuild()
