# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import typer

simmate_chatbot_app = typer.Typer(rich_markup_mode="markdown")


@simmate_chatbot_app.callback(no_args_is_help=True)
def base_command():
    """
    Welcome to the command-line interface for Simmate's LLM chatbot!
    """
    # When we call the command "simmate-chatbot" this is where we start, and
    # it then looks for all other functions that have the decorator
    # "@simmate_chatbot_app.command()" to decide what to do from there.
    pass


@simmate_chatbot_app.command()
def run_server(port: int = 8501, address: str = None):
    """
    Runs the local test server.

    While this command is running, you can then view the chatbot web UI
    at http://localhost:8501 (aka http://127.0.0.1:8501/)

    This is a streamlit app, so this is really just a wrapper around the
    command: `streamlit run web_service.py`
    """
    import subprocess

    # The streamlit app we serve is stored in this module so we need the file
    # path to it, and then pass that to the streamlit command
    module_directory = Path(__file__).absolute().parent
    server_file = module_directory / "web_service.py"

    # OPTIMIZE: consider using a config file instead
    #   https://docs.streamlit.io/library/advanced-features/configuration
    #   https://docs.streamlit.io/library/advanced-features/theming
    extra_config = (
        '--theme.backgroundColor="#fafbfe" ' '--theme.primaryColor="#0072ce" '
    )
    if port != 8501:
        extra_config += f"--server.port={port} "
    if address:
        extra_config += f"--server.address={address} "  # 0.0.0.0 for prod

    logging.info("Setting up local test server...")
    subprocess.run(
        f"streamlit run {server_file} {extra_config}",
        shell=True,
    )
