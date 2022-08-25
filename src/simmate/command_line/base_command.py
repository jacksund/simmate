# -*- coding: utf-8 -*-

"""
This defines the base "simmate" command that all other commands stem from.
"""

import logging
from pathlib import Path

import typer

from simmate.command_line.database import database_app
from simmate.command_line.utilities import utilities_app
from simmate.command_line.workflow_engine import workflow_engine_app
from simmate.command_line.workflows import workflows_app

simmate_app = typer.Typer(rich_markup_mode="markdown")


@simmate_app.callback(no_args_is_help=True)
def base_command():
    """
    This is the base command that all other Simmate commands stem from
    :fire::fire::rocket:

    ---------

    If you are a beginner to the command line, be sure to start with
    [our tutorials](https://jacksund.github.io/simmate/getting_started/overview/).
    Below you will see a list of sub-commands to try. For example, you can run `simmate
    database --help` to learn more about it.

    \n
    TIP: Many Simmate commands are long and verbose. You can use `--install-completion`
    to add ipython-like autocomplete to your shell.

    """
    # When we call the command "simmate" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate.command()"
    # to decide what to do from there.
    pass


@simmate_app.command()
def run_server():
    """
    Runs a local test server for the Simmate website interface

    While this command is running, you can then view the working website
    at http://127.0.0.1:8000/

    This command is exactly the same as running:

    `django runserver --settings=simmate.configuration.django.settings`
    """

    # BUG: logging prints ugly duplicates as it sets up simmate and also a
    # static server for it.
    logging.warning(
        "Seeing duplicate messages is normal and expected. "
        "This is because the test server sets up + tears down Simmate on a cycle."
    )

    from django.core.management import call_command

    from simmate.database import connect

    call_command("runserver")


@simmate_app.command()
def start_project(project_name: Path):
    """
    Creates a new folder and fills it with an example project to
    get you started with custom Simmate workflows/datatables
    """

    import logging

    from django.core.management import call_command

    from simmate import configuration  # needed just for the filepath

    # This directory is where our template folder is located. We find this
    # by looking at the import path to see where python installed it.
    config_directory = Path(configuration.__file__).absolute().parent

    # We add on "project_template" to this file path as that's our full template
    template_directory = config_directory / "example_project"

    # we now make the project folder using our template directory.
    # Note, we are using Django's "startproject" command even though we are just
    # copying files over. This might be overkill but it gets the job done.
    call_command(
        "startproject",
        project_name,
        template=str(template_directory),
        extensions=["toml", "py"],
    )

    # grab the full path to the new project for the user to see
    new_project_directory = Path.cwd() / project_name

    # also navigate to the user's ~/simmate/applications.yaml file and we
    # want to add a new line at the end of it (or create the file if it isn't
    # there yet)
    apps_yaml = Path.home() / "simmate" / "applications.yaml"
    new_line = "\nexample_app.apps.ExampleAppConfig"  # \n ensures a new line

    # If the file exists, we append this line to the end of the file. Otherwise,
    # we create a new file and add the line!
    with apps_yaml.open("a+") as file:
        file.write(new_line)
    # Let the user know what we did and how to continue.
    logging.info(
        "\n\tSuccessfully made a new project! \n\t"
        f"You'll find it at {new_project_directory}\n\n"
        "\tBe sure to go through the README file in your new project.\n"
    )


# # All commands are organized into other files, so we need to manually register
# # them to our base "simmate" command here.
simmate_app.add_typer(database_app, name="database")
simmate_app.add_typer(workflows_app, name="workflows")
simmate_app.add_typer(workflow_engine_app, name="workflow-engine")
simmate_app.add_typer(utilities_app, name="utilities")
