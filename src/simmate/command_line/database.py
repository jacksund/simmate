"""
This defines commands for managing your Simmate database. All commands are
accessible through the `simmate database` command.
"""

import typer

from simmate.command_line.utilities import AlphabeticalGroup
from simmate.utils import logger

database_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)


@database_app.callback(no_args_is_help=True)
def base_command():
    """
    Commands for managing the Simmate database, including Postgres setup,
    schema migrations, and data I/O.
    """


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
    Stops the Postgres database Docker container.
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
    use_template: bool = typer.Option(
        None,
        "--use-template/--no-use-template",
        help="Whether to copy the `<name>_template` database made by `simmate database snapshot` (Postgres only). If not provided and the template exists, you will be prompted.",
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
            "involve a ~4GB \ndownload and will unpack to ~35GB."
        )

    from simmate.database import connect
    from simmate.database.utils import reset_database

    reset_database(use_prebuilt=use_prebuilt, use_template=use_template)


@database_app.command()
def snapshot():
    """
    Copies your database to `<name>_template` (Postgres only), which `reset`
    can then start from. Any existing template is replaced.

    This is useful in local development to avoid reloading large datasets
    after every reset. Make sure nothing else is connected to the database.
    """

    from simmate.database.utils import snapshot_database

    snapshot_database()


@database_app.command()
def update():
    """
    Updates the database schema to reflect any recent changes to Django models.
    """

    from simmate.database import connect
    from simmate.database.utils import update_database

    update_database()


@database_app.command()
def load(
    app_name: str = typer.Argument(
        ...,
        help="The name of the app to load data for (e.g., 'cod').",
    ),
    source: str = typer.Option(
        "direct",
        help="Where to download the data from. Options are 'direct' or 'archive'.",
    ),
):
    """
    Downloads and loads third-party data for a specific app into the database.
    """

    from simmate.database import connect
    from simmate.database.utils import download_app_data

    download_app_data(app_name, source=source)


@database_app.command()
def load_test_data(
    app_labels: list[str] = typer.Argument(
        None,
        help="The apps to load (e.g. inventory_management). Defaults to all apps.",
    ),
):
    """
    Loads fake data (from each app's `test/fake_data.zip`) into the database.

    This is meant for an empty dev database, so that UIs can be explored
    without real data. Run `simmate database reset` first if needed.
    """
    from django.apps import apps

    from simmate.database import connect
    from simmate.database.utils import get_fake_data_path, load_fake_data

    if not app_labels:
        app_labels = [
            config.label
            for config in apps.get_app_configs()
            if get_fake_data_path(config.label).exists()
        ]

    for app_label in app_labels:
        logger.info(f"Loading fake data for '{app_label}'...")
        load_fake_data(app_label)

    logger.info("Done! :sparkles:")


@database_app.command()
def prebuild():
    """
    Creates a date-stamped zip file of the current SQLite3 database.
    """
    from simmate.database.utils import create_prebuild

    create_prebuild()
