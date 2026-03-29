# -*- coding: utf-8 -*-

"""
This defines the base "simmate" command that all other commands stem from.
"""

import logging
from pathlib import Path

import typer

from simmate.command_line.compute import compute_app
from simmate.command_line.config import config_app
from simmate.command_line.database import database_app
from simmate.command_line.dev import dev_app
from simmate.command_line.utils import utils_app
from simmate.command_line.workflows import workflows_app

simmate_app = typer.Typer(
    rich_markup_mode="markdown",
    add_completion=False,
)


@simmate_app.callback(no_args_is_help=True)
def base_command():
    """
    :sparkles: Simmate: A full-stack framework for chemistry research :sparkles:

    This is the base command that all other Simmate commands stem from. For
    help with a specific command group, use `simmate <group> --help`
    (e.g., `simmate database --help`).
    """
    pass


@simmate_app.command()
def version():
    """
    Displays the currently installed version of Simmate and checks for updates.
    """
    import simmate
    from simmate.utils import get_latest_version

    print(f"Installed version: v{simmate.__version__}")
    print(f"Newest available:  v{get_latest_version()}")


@simmate_app.command()
def run_server(
    port: int = typer.Option(
        8000,
        help="The port on which to run the local server. Default is 8000.",
    )
):
    """
    Starts a local development server for the Simmate Web UI.

    While the server is running, you can access the interface in your browser
    at http://localhost:8000/.

    This server is intended for local testing and data exploration. It should
    **not** be used for production deployments.
    """

    import subprocess

    from simmate.config import settings
    from simmate.website.core.utils import download_ketcher

    logging.info("Setting up local test server...")

    # Ensure Ketcher is available locally to avoid CORS issues
    if not settings.website.get("chemdraw_js", False):
        download_ketcher()

    subprocess.run(
        f"django-admin runserver {port} --settings=simmate.config.django.settings --insecure --noreload",
        shell=True,
    )


@simmate_app.command()
def start_project():
    """
    Initializes a new Simmate project directory from a template.

    This command creates a `my_simmate_project` folder in your current directory,
    pre-populated with an example application structure. This is the recommended
    starting point for building custom Simmate apps.
    """

    import logging
    import shutil

    from simmate import config  # needed for the filepath

    # This directory is where our template folder is located. We find this
    # by looking at the import path to see where python installed it.
    config_directory = Path(config.__file__).absolute().parent

    # We add on "project_template" to this file path as that's our full template
    template_directory = config_directory / "example_project"

    # grab the full path to the new project for the user to see
    new_project_directory = Path.cwd() / "my_simmate_project"

    # copy the directory over
    shutil.copytree(template_directory, new_project_directory)

    # Let the user know what we did and how to continue.
    logging.info(
        "Successfully made a new project! \n\n"
        f"You'll find it at {new_project_directory}\n\n"
        "Note, this project's app has not yet been named, installed, or "
        "registered yet. Follow along with our tutorial to complete these steps."
    )


# # All commands are organized into other files, so we need to manually register
# # them to our base "simmate" command here.
simmate_app.add_typer(config_app, name="config")
simmate_app.add_typer(database_app, name="database")
simmate_app.add_typer(dev_app, name="dev")
simmate_app.add_typer(compute_app, name="compute")
simmate_app.add_typer(workflows_app, name="workflows")
simmate_app.add_typer(utils_app, name="utils")
