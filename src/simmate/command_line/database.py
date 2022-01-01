# -*- coding: utf-8 -*-

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
def reset(confirm_delete):
    """Removes any existing data and sets up a clean database."""

    # make sure the user knows what they are doing and actually wants to continue
    if not confirm_delete:
        click.confirm(
            "Note that this deletes your current database and cannot be undone. "
            "We highly recommend you make a copy of your database before doing this. "
            "Do you still want to continue?",
            abort=True,
        )
    # We can now proceed with reseting the database
    click.echo("Removing database and rebuilding...")

    from simmate.configuration.django.database import reset_database

    reset_database()

    # Let the user know everything succeeded
    click.echo("Success! Your database has been reset.")


@database.command()
def update():
    """Updates the database with any changes made."""

    # check Django if there are any updates to be made
    click.echo("Checking for updates...")

    from simmate.configuration.django.database import update_database

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

    from simmate.configuration.django.database import dump_database_to_json

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

    from simmate.configuration.django.database import load_database_from_json

    load_database_from_json(filename=filename)

    # Let the user know everything succeeded
    click.echo(
        f"Success! You now have all the data from {filename} available in your database."
    )
