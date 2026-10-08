# -*- coding: utf-8 -*-

"""
This defines commands for the Simmate website. All commands are accessible
through the `simmate website` command.
"""

import logging

import typer

from simmate.command_line.utilities import AlphabeticalGroup

website_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)


@website_app.callback(no_args_is_help=True)
def website():
    """
    Commands for running the Simmate Web UI.
    """
    pass


@website_app.command()
def start(
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
