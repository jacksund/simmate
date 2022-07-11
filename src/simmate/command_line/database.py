# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate database. All commands are 
accessible through the `simmate database` command.
"""

import click


@click.group()
def database():
    """A group of commands for managing your database."""
    pass


@database.command()
@click.option(
    "--confirm-delete",
    is_flag=True,
    help="automatically confirms that you want to delete your existing database",
)
@click.option(
    "--use-prebuilt",
    default=None,
    type=bool,
    help="automatically says yes/no a prebuilt database (only applies if using sqlite)",
)
def reset(confirm_delete, use_prebuilt):
    """Removes any existing data and sets up a clean database."""

    # make sure the user knows what they are doing and actually wants to continue
    if not confirm_delete:
        click.confirm(
            "Note that this deletes your current database and cannot be undone. "
            "We highly recommend you make a copy of your database before doing this. "
            "Do you still want to continue?",
            abort=True,
        )

    # if the user has a SQLite3 backend, ask if they'd like to use a prebuilt
    # database to begin
    from simmate.configuration.django.settings import DATABASES

    using_sqlite = DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    if using_sqlite and use_prebuilt == None:
        use_prebuilt = click.confirm(
            "It looks like you are using the default database backend (sqlite3). "
            "Would you like to use a prebuilt-database with all third-party data "
            "already loaded? If this is the first time you using the prebuild, "
            "this will involve a ~3GB download and will unpack to roughly 7GB. A "
            "backup of the download will be stored as well (so another ~3GB disk "
            "space will be used). We recommend answering 'yes' for beginners."
        )

    # We can now proceed with reseting the database
    click.echo("Removing database and rebuilding...")

    from simmate.database import connect
    from simmate.database.utilities import reset_database

    reset_database(use_prebuilt=use_prebuilt)

    # Let the user know everything succeeded
    click.echo("Success! Your database has been reset.")


@database.command()
def update():
    """Updates the database with any changes made."""

    # check Django if there are any updates to be made
    click.echo("Checking for updates...")

    from simmate.database import connect
    from simmate.database.utilities import update_database

    update_database()

    # Let the user know everything succeeded
    click.echo("Success! Your database tables are now up to date.")


@database.command()
@click.option(
    "--filename",
    "-f",
    default="database_dump.json",
    help="the file to write the all the JSON data to",
)
def dumpdata(filename):
    """Takes the Simmate database and writes it to a json file."""

    # Begin writing the database to the json file.
    click.echo("Writing all data to JSON...")

    from simmate.database import connect
    from simmate.database.utilities import dump_database_to_json

    dump_database_to_json(filename=filename)

    # Let the user know everything succeeded
    click.echo(
        f"Success! You should now see the file {filename} with all of your data."
    )


@database.command()
@click.option(
    "--filename",
    "-f",
    default="database_dump.json",
    help="the file to load the all the JSON data from",
)
def loaddata(filename):
    """Takes a JSON database and loads it into the Simmate database."""

    # Begin writing the database to the json file.
    click.echo("Loading all data from JSON...")

    from simmate.database import connect
    from simmate.database.utilities import load_database_from_json

    load_database_from_json(filename=filename)

    # Let the user know everything succeeded
    click.echo(
        f"Success! You now have all the data from {filename} available in your database."
    )


@database.command()
@click.option(
    "--parallel",
    is_flag=True,
    help="(not allowed for SQLite3) loads data using parallel processing",
)
def load_remote_archives(parallel):
    """
    Goes through all third-party databases and loads their most recent remote
    archives (if available). This utility helps with initializing a new
    database build.

    WARNING:
    This can take several hours to run and there is no pause/continuation
    implemented. This runs substantially faster when you are using a cloud
    database backend (e.g. Postgres) and use the `--parallel` flag.

    If you are using SQLite, we highly recommend using loading the default build
    when you run `simmate database reset` instead.d.
    """

    from simmate.database import connect
    from simmate.database.third_parties import load_remote_archives

    load_remote_archives(parallel=parallel)
    click.echo("Success! Your database now contains all third-party data.")


# explicitly list functions so that pdoc doesn't skip them
__all__ = [
    "database",
    "reset",
    "update",
    "dumpdata",
    "loaddata",
    "load_remote_archives",
]
