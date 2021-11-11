# -*- coding: utf-8 -*-

import click


@click.command()
def run_server():
    """
    This runs a website test server locally for Simmate. You can then view the
    working website at http://127.0.0.1:8000/

    This command is exactly the same as running...

    django runserver --settings=simmate.configuration.django.settings
    """

    from simmate.configuration.django import setup_full  # loads settings
    from django.core.management import call_command

    # make sure we unpacked our material_kit assets before running
    from simmate.configuration.django.assets import unpack_assets

    unpack_assets()

    call_command("runserver")
