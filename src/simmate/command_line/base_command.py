# -*- coding: utf-8 -*-

"""
This defines the base "simmate" command that all other commands stem from.
"""

import typer

from simmate.command_line.database import database_app

# from simmate.command_line.run_server import run_server
# from simmate.command_line.start_project import start_project
from simmate.command_line.utilities import utilities_app

# from simmate.command_line.workflow_engine import workflow_engine
# from simmate.command_line.workflows import workflows


simmate_app = typer.Typer(rich_markup_mode="markdown")


@simmate_app.callback()
def base_command():
    """
    This is the base command that all other Simmate commands stem from
    :fire::fire::rocket:


    If you are a beginner to the command line, be sure to start with
    [our tutorials](https://github.com/jacksund/simmate/tree/main/tutorials).


    Below you will see a list of sub-commands to try. For example, you can run `simmate
    database --help` to learn more about it.

    """
    # When we call the command "simmate" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate.command()"
    # to decide what to do from there.
    pass


# typer_click_object = typer.main.get_command(simmate_app)

# # All commands are organized into other files, so we need to manually register
# # them to our base "simmate" command here.
simmate_app.add_typer(database_app, name="database")
# simmate_app.add_typer(workflows_app, name="workflows")
# simmate_app.add_typer(workflow_engine_app, name="workflow_engine")
# simmate_app.add_typer(run_server_app, name="run_server")
# simmate_app.add_typer(start_project_app, name="start_project")
simmate_app.add_typer(utilities_app, name="utilities")

# # explicitly list functions so that pdoc doesn't skip them
# __all__ = ["simmate"]
