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
    """A group of commands for managing your database"""
    pass


@database_app.command()
def reset(confirm_delete: bool = False, use_prebuilt: bool = None):
    """
    Removes any existing data and sets up a clean database


    - `--confirm-delete`: automatically confirms you want to delete the
    existing database.
    :warning::warning: Use this with caution.:warning::warning:

    - `--use-prebuilt` and `--no-use-prebuilt`: automatically say yes/no to a
    prebuilt database. This only applies if you are using sqlite.
    """
    from simmate.configuration import settings

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
            "Would you like to use a prebuilt-database with all third-party data "
            "already loaded? \n"
            "If this is the first time you using the prebuild, this will "
            "involve a ~1.5GB \ndownload and will unpack to roughly 5GB.\n\n"
            "We recommend answering 'yes' for beginners."
        )

    from simmate.database import connect
    from simmate.database.utilities import reset_database

    reset_database(use_prebuilt=use_prebuilt)


@database_app.command()
def update():
    """Updates the database with any changes made"""

    from simmate.database import connect
    from simmate.database.utilities import update_database

    update_database()


@database_app.command()
def dump_data(filename: Path = "database_dump.json", exclude: list[str] = []):
    """
    Takes the Simmate database and writes it to a json file

    - `--filename` is the file to write the all the JSON data to
    """

    from simmate.database import connect
    from simmate.database.utilities import dump_database_to_json

    dump_database_to_json(filename=filename, exclude=exclude)


@database_app.command()
def load_data(filename: Path = "database_dump.json"):
    """
    Takes a JSON database and loads it into the Simmate database

    - `--filename` is the file to load the all the JSON data from
    """

    from simmate.database import connect
    from simmate.database.utilities import load_database_from_json

    load_database_from_json(filename=filename)


@database_app.command()
def load_remote_archives(parallel: bool = False):
    """
    Loads all third-party data into the database

    This utility helps with initializing a new database build.

    :WARNING:
    This can take several hours to run and there is no pause/continuation
    implemented. This runs substantially faster when you are using a cloud
    database backend (e.g. Postgres) and use the `--parallel` flag.

    If you are using SQLite, we highly recommend using loading the prebuild
    when you run `simmate database reset` instead.

    - `--parallel`: (not allowed for SQLite3) loads data using parallel processing
    """

    from simmate.database import connect
    from simmate.database.third_parties import load_remote_archives

    load_remote_archives(parallel=parallel)
