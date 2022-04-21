# -*- coding: utf-8 -*-

"""
This defines the command for running a test-server locally.
"""

import click


@click.command()
def run_server():
    """
    This runs a website test server locally for Simmate. You can then view the
    working website at http://127.0.0.1:8000/

    This command is exactly the same as running...

    django runserver --settings=simmate.configuration.django.settings
    """

    from simmate.database import connect
    from django.core.management import call_command

    call_command("runserver")


# explicitly list functions so that pdoc doesn't skip them
__all__ = ["run_server"]
