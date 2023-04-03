# -*- coding: utf-8 -*-

import logging
import shutil
from pathlib import Path

from django.apps import apps
from django.core.management import call_command

from simmate.configuration.django.settings import DATABASES

# Lists off which apps to update/create. By default, I do all apps that are installed
# so this list is grabbed directly from django. I also grab the CUSTOM_APPS to
# check for user-installed applications.
APPS_TO_MIGRATE = list(apps.app_configs.keys())


def update_database(apps_to_migrate=APPS_TO_MIGRATE, show_logs: bool = True):
    # check Django if there are any updates to be made
    if show_logs:
        logging.info("Checking for and applying updates...")

    # execute the following commands to update the database
    call_command("makemigrations", *apps_to_migrate)
    call_command("migrate")

    # Let the user know everything succeeded
    if show_logs:
        logging.info("Success! Your database tables are now up to date. :sparkles:")


def reset_database(apps_to_migrate=APPS_TO_MIGRATE, use_prebuilt=False):
    # BUG: Why doesn't call_command("flush") do this? How is it different?

    # We can now proceed with reseting the database
    logging.info("Removing database and rebuilding...")

    # BUG: this is only for SQLite3 and Postgres
    # If I wish to add FULL functionality of all DBs, I could consider
    # wrapping the django-extensions function for this instead:
    #   https://django-extensions.readthedocs.io/en/latest/reset_db.html
    # An example command to call this (when django-extensions is installed) is...
    #   django-admin reset_db --settings=simmate.configuration.django.settings
    # Note: this does not remove migration files or reapply migrating after

    # Check which
    using_sqlite = DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    using_postgres = DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    if using_sqlite:
        # grab the location of the database file. I assume the default
        # database for now.
        db_filename = DATABASES["default"]["NAME"]

        # delete the sqlite3 database file if it exists
        if db_filename.exists():
            db_filename.unlink()

    elif using_postgres:
        # We do this with an independent postgress connection, rather than through
        # django so that we can close everything down easily.
        import psycopg2

        # Setup Postgres connection
        # Postgres requires a 'maintenance database' that we connect to while
        # we add/drop the table. For most cases, such as building a new database
        # through PgAdmin or a Docker image, the maintenance database will be
        # named "postgres". For Digitial Ocean, it will be named "defaultdb".
        # As a last resort, we can also check if there is a database matching
        # the name of the user. We iterate through these common cases until
        # we find one that works, and then warn the user if things fail.
        connection = None
        for maintenance_db_name in [
            "postgres",
            "defaultdb",
            DATABASES["default"]["USER"],
        ]:
            try:
                connection = psycopg2.connect(
                    host=DATABASES["default"]["HOST"],
                    database=maintenance_db_name,
                    user=DATABASES["default"]["USER"],
                    password=DATABASES["default"]["PASSWORD"],
                    port=DATABASES["default"]["PORT"],
                )
            except psycopg2.OperationalError as error:
                if f'"{maintenance_db_name}" does not exist' in str(error):
                    continue  # just jump to trying the next db name
                # otherwise we might a password auth issue or something else
                raise error

            # exit loop as soon as we have a working connection
            if connection:
                break

        # ensure the loop above found a working connection
        if not connection:
            raise Exception(
                "Postgres requires a 'maintenance database' that we connect to "
                "while we add/drop/reset the database that you'd like to use. "
                "That database can stay empty, but it's important to be present. "
                "Simmate was unable to detect your maintenance database, which "
                "is why you're seeing this error. To fix this, make sure you have "
                "a database named either 'postgres', 'defaultdb', or one that has "
                "an identical name to your username. Create this database on your "
                "postgres server with a SQL command such as 'CREATE DATABASE "
                "defaultdb' and then retry your simmate command."
            )

        # In order to delete a full database, we need to isolate this call
        connection.set_isolation_level(0)

        # Open connection cursor to perform database operations
        cursor = connection.cursor()

        # Build out database extensions and tables
        db_name = DATABASES["default"]["NAME"]
        cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}";')
        # BUG: if others are connected I could add 'WITH (FORCE)' above.
        # For now, I don't use this but should consider adding it for convenience.
        # I think this is buggy with older versions of postgres (like RDkit),
        # so I hold off on this for now.
        cursor.execute(f'CREATE DATABASE "{db_name}";')

        # Make the changes to the database persistent
        connection.commit()

        # Close communication with the database
        cursor.close()
        connection.close()

    elif not using_sqlite and not using_postgres:
        logging.warning(
            "reseting your database is only supported for SQLite and Postgres."
            " Make sure you only use this function when initially building your "
            "database and not after."
        )

    # go through each app directory and delete all folders named 'migrations'
    for app_name, app_config in apps.app_configs.items():
        # Skip if the app was not requested
        if app_config.label not in apps_to_migrate:
            continue

        migration_dir = Path(app_config.path) / "migrations"
        # BUG: I need a good way to avoid deleting initial migrations that
        # do things like register extensions.
        # Maybe have these migrations listed as 0000_setup.py and then delete
        # everything after?
        # Maybe skip folders that contain a 0001_setup.py?
        skip_deletes = ["rdkit", "datasets"]
        if migration_dir.exists() and migration_dir.parent.name not in skip_deletes:
            shutil.rmtree(migration_dir)
            continue

    # now update the database based on the registered models
    update_database(apps_to_migrate, show_logs=False)

    # instead of building the database from scratch, we instead download a
    # prebuilt database file.
    if using_sqlite and use_prebuilt:
        from simmate.database.third_parties import load_default_sqlite3_build

        logging.info("Setting up prebuilt database...")
        load_default_sqlite3_build()

    # Otherwise we leave the empty database.
    # Because this is our first time building the database, we also want to
    # load the Spacegroup metadata for us to query Structures by.
    else:
        from simmate.database.base_data_types import Spacegroup

        logging.info("Loading default data")
        Spacegroup._load_database_from_toolkit()

    # Let the user know everything succeeded
    logging.info("Success! Your database has been reset. :sparkles:")


def dump_database_to_json(filename="database_dump.json", exclude=[]):
    # Begin writing the database to the json file.
    logging.info("Writing all data to JSON...")

    # execute the following commands to write the database to a json file
    call_command("dumpdata", output=filename, exclude=exclude)

    # Let the user know everything succeeded
    logging.info(
        f"Success! You should now see the file {filename} with all of your data."
    )


def load_database_from_json(filename="database_dump.json"):
    # Begin writing the database to the json file.
    logging.info("Loading all data from JSON...")

    # OPTIMIZE: this function is very slow. Consider speed-up options such as
    # making this function a transaction or manually writing a bulk_create. It
    # actually looks like django ORM takes up most of the time tough, and the actual
    # database queries are not the bottleneck...

    # execute the following commands to build the database
    # BUG: contenttypes gives issues because a migrated database already has these
    # set. Simply ignore this table and everything works. The contenttypes is
    # simply a table that lists all of our different models.
    call_command("loaddata", filename, exclude=["contenttypes"])

    # Let the user know everything succeeded
    logging.info(
        f"Success! You now have all the data from {filename} available in your database."
    )


# BUG: This function isn't working as intended
# def graph_database(filename="database_graph.png"):

#     # using django-extensions, we want to make an image of all the available
#     # tables in our database as well as their relationships.

#     # This is the equivalent of running the following command:
#     #   django-admin graph_models -a -o image_of_models.png --settings=...
#     call_command("graph_models", output=filename, all_applications=True, layout="fdp")
