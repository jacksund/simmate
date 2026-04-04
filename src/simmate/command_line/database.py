# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate database. All commands are
accessible through the `simmate database` command.
"""

from pathlib import Path

import typer

database_app = typer.Typer(rich_markup_mode="markdown")


@database_app.callback(no_args_is_help=True)
def base_command():
    """
    Commands for managing the Simmate database, including Postgres setup,
    schema migrations, and data I/O.
    """
    pass


@database_app.command()
def start(
    password: str = typer.Option(
        "postgres",
        help="The password for the `postgres` user in the Docker container.",
    ),
    port: int = typer.Option(
        5432,
        help="The port to expose the database on. Defaults to 5432.",
    ),
):
    """
    Starts a Postgres database instance in a Docker container.

    This is a quick way to set up a robust database for local use without
    manual installation.
    """

    from simmate.database.utils import start_postgres_docker

    start_postgres_docker(password=password, port=port)


@database_app.command()
def stop():
    """
    Stops and removes the Postgres database Docker container.
    """
    from simmate.database.utils import stop_postgres_docker

    stop_postgres_docker()


@database_app.command()
def reset(
    confirm_delete: bool = typer.Option(
        False,
        "--confirm-delete",
        help="Automatically confirm that you want to delete and reset the existing database.",
    ),
    use_prebuilt: bool = typer.Option(
        None,
        "--use-prebuilt/--no-use-prebuilt",
        help="Whether to use a pre-populated database (SQLite only). If not provided, you will be prompted.",
    ),
):
    """
    Wipes the existing database and initializes a fresh, empty schema.

    :warning: **This action is irreversible.** All your data will be lost. :warning:
    """
    from simmate.config import settings

    database_name = str(settings.database.name)
    print(f"\nUsing {database_name}")

    # make sure the user knows what they are doing and actually wants to continue
    if not confirm_delete:
        typer.confirm(
            "\nWARNING: This deletes your current database and cannot be undone. \n"
            "We highly recommend you make a copy of your database before doing this. \n\n"
            "Do you still want to continue?",
            abort=True,
        )

    # if the user has a SQLite3 backend, ask if they'd like to use a prebuilt
    # database to begin
    if settings.database_backend == "sqlite3" and use_prebuilt is None:
        use_prebuilt = typer.confirm(
            "\nIt looks like you are using the default database backend (sqlite3). \n"
            "Would you like to use a prebuilt-database with third-party data "
            "already loaded in? \n"
            "If this is the first time you using the prebuild, this will "
            "involve a ~3GB \ndownload and will unpack to ~20GB.\n\n"
            "We recommend answering 'yes' for beginners."
        )

    from simmate.database import connect
    from simmate.database.utils import reset_database

    reset_database(use_prebuilt=use_prebuilt)


@database_app.command()
def update():
    """
    Updates the database schema to reflect any recent changes to Django models.
    """

    from simmate.database import connect
    from simmate.database.utils import update_database

    update_database()


@database_app.command()
def download(
    app_name: str = typer.Argument(
        ...,
        help="The name of the app to download data for (e.g., 'cod').",
    ),
    source: str = typer.Option(
        "direct",
        help="Where to download the data from. Options are 'direct' or 'archive'.",
    ),
):
    """
    Downloads and populates the database with third-party data for a specific app.
    """

    from simmate.database import connect
    from simmate.database.utils import download_app_data

    download_app_data(app_name, source=source)


@database_app.command()
def dump_data(
    filename: Path = typer.Option(
        "database_dump.json",
        help="The JSON file where the database contents should be written.",
    ),
    exclude: list[str] = typer.Option(
        [],
        help="List of apps or models to exclude from the dump. Use `--exclude example` for each item.",
    ),
):
    """
    Exports the current database contents to a JSON file.
    """

    from simmate.database import connect
    from simmate.database.utils import dump_database_to_json

    dump_database_to_json(filename=filename, exclude=exclude)


@database_app.command()
def load_data(
    filename: Path = typer.Option(
        "database_dump.json",
        help="The JSON file containing the database contents to load.",
    )
):
    """
    Imports database contents from a JSON file.
    """

    from simmate.database import connect
    from simmate.database.utils import load_database_from_json

    load_database_from_json(filename=filename)
