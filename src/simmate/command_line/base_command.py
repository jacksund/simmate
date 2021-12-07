# -*- coding: utf-8 -*-

import click

from simmate.command_line.database import database
from simmate.command_line.workflows import workflows
from simmate.command_line.workflow_engine import workflow_engine
from simmate.command_line.run_server import run_server
from simmate.command_line.start_project import start_project


@click.group()
def simmate():
    """
    This is the base command that all others stem from.

    If you are a beginner for the command line, take a look at our tutorial:
        << TODO: insert link >>

    """
    # When we call the command "simmate" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate.command()"
    # to decide what to do from there.
    pass


# All commands are organized into other files, so we need to manually register
# them to our base "simmate" command here.
simmate.add_command(database)
simmate.add_command(workflows)
simmate.add_command(workflow_engine)
simmate.add_command(run_server)
simmate.add_command(start_project)
