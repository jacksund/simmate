# -*- coding: utf-8 -*-

import click

from simmate.command_line.database import database
from simmate.command_line.workflows import workflows


@click.group()
def simmate():
    """
    This is the base command that all others stem from.

    If you are brand-new to the command line, take a look at our tutorial:
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

# @database.command()
# @click.option("--count", default=1, help="Number of greetings.")
# @click.option("--name", prompt="Your name", help="The person to greet.")
# def hellodata(count, name):
#     """Simple program that greets NAME for a total of COUNT times."""
#     for x in range(count):
#         click.echo(f"Hello {name}!")
