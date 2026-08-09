# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import typer

simmate_analysis_dashboard_app = typer.Typer(rich_markup_mode="markdown")


@simmate_analysis_dashboard_app.callback(no_args_is_help=True)
def base_command():
    """
    Commands for managing the Simmate Analysis Dashboard, a Streamlit-based
    interface for data visualization and analysis.
    """
    pass


@simmate_analysis_dashboard_app.command()
def run_server(
    port: int = typer.Option(
        8501,
        help="The port to run the dashboard on. Default is 8501.",
    ),
    address: str = typer.Option(
        None,
        help="The network address to bind the server to (e.g., '0.0.0.0' for all interfaces).",
    ),
):
    """
    Starts a local Streamlit server to host the Analysis Dashboard.

    While the server is running, you can access the dashboard in your browser
    at http://localhost:8501/.
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
        '--theme.backgroundColor="#fafbfe" '
        '--theme.primaryColor="#0072ce" '
        # '--server.maxUploadSize=500'
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
