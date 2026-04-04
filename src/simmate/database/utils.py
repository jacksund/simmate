# -*- coding: utf-8 -*-

import logging
import shutil
import subprocess
import urllib
import zipfile
from datetime import datetime
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.db.utils import DatabaseError

from simmate.config import settings
from simmate.utils import get_directory

# Lists off which apps to update/create. By default, I do all apps that are installed
# so this list is grabbed directly from django. I also grab the CUSTOM_APPS to
# check for user-installed applications.
APPS_TO_MIGRATE = list(apps.app_configs.keys())


def batch_bulk_create(batch_size: int = 1000):
    """
    Decorator for the `load_source_data` classmethod on DatabaseTables.
    Expects the wrapped method to be a generator that yields database objects.
    This handles creating the objects in batches using `bulk_create`.
    """

    def decorator(func):
        import logging
        from functools import wraps

        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            logging.info(f"Generating database objects for {cls.table_name}...")
            db_objs = []

            for obj in func(cls, *args, **kwargs):
                if obj is None:
                    continue
                db_objs.append(obj)
                if len(db_objs) >= batch_size:
                    cls.objects.bulk_create(
                        db_objs,
                        batch_size=batch_size,
                        ignore_conflicts=True,
                    )
                    db_objs = []  # reset for next batch

            # save any remaining
            if db_objs:
                cls.objects.bulk_create(
                    db_objs,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

            # Call post-source load if implemented
            if hasattr(cls, "_post_source_load"):
                cls._post_source_load()

            logging.info("Done!")

        return wrapper

    return decorator


def check_db_conn(original_function: callable):
    """
    A decorator that catches errors such as "close connection" failures and
    retries with a new connection.

    ## Example use:
    ``` python
    @check_db_conn
    def example():
        return 12345 # some fxn that makes database calls
    ```
    """
    # BUGFIX: for processes (e.g. workflows) that take >1hr, the database
    # connection to postgres can be dropped/terminated. So we need to catch
    # this and make a new connection.
    #   https://github.com/jacksund/simmate/issues/364

    # New feature in Django worth exploring if this becomes an issue again.
    # However, this is only for web views... not local dev/runs:
    #   https://docs.djangoproject.com/en/4.1/ref/settings/#conn-health-checks

    def wrapper(*args, **kwargs):
        # On our first try, just use default method and existing connection
        try:
            return original_function(*args, **kwargs)

        # This 2nd attempt is an exact retry where we grab a new db connection
        # Fix is from:
        #   https://stackoverflow.com/questions/48329685
        except DatabaseError as error:
            logging.critical(error)
            logging.info("retrying with new db connection")

            # Note, this import needs to be done locally! Having it imported
            # above causes pickling errors.
            #   see https://github.com/jacksund/simmate/issues/410
            from django.db import connection as db_connection

            db_connection.connect()

            # retry the function call
            return original_function(*args, **kwargs)

    return wrapper


def update_database(
    apps_to_migrate: list[str] = APPS_TO_MIGRATE,
    show_logs: bool = True,
):
    # check Django if there are any updates to be made
    if show_logs:
        logging.info("Checking for and applying updates...")

    # execute the following commands to update the database
    call_command("makemigrations", *apps_to_migrate)
    call_command("migrate")

    # Let the user know everything succeeded
    if show_logs:
        logging.info("Success! Your database tables are now up to date. :sparkles:")


def postgres_connect_maintenance_db():
    """
    A convenience method to establish a connection to a hosted postgres database
    for adding and deleting tables
    """
    import psycopg2

    # grab postges config parameters, *excluding* the database name and engine.
    # Also anything in the OPTIONS is an extra kwarg that we flatten and add
    config = settings.database
    config.pop("name")
    config.pop("engine")  # assumed to be postgres (checked elsewhere)
    config.update(config.pop("options", {}))  # ex: sslmode would be here

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
        settings.database.user,
    ]:
        try:
            connection = psycopg2.connect(
                database=maintenance_db_name,
                **config,
            )
        except psycopg2.OperationalError as error:
            if f'"{maintenance_db_name}" does not exist' in str(error):
                continue  # just jump to trying the next db name
            # otherwise we might a password auth issue or something else
            raise error

        # exit loop as soon as we have a working connection
        if connection:
            # catch misuse where the user wants to "reset" the maintenence db
            if maintenance_db_name == settings.database.name:
                raise Exception(
                    "Postgres requires a 'maintenance database' that we connect to "
                    "while we add/drop/reset the database that you'd like to use. "
                    "That database can stay empty, but it's important to be present. "
                    "Howeveer, it looks like your are trying to reset your maintenance "
                    f"database ('{maintenance_db_name}') which is not allowed. "
                    "Please update your 'settings.database.name' to something else."
                )
            break

    # ensure the loop above found a working connection
    if connection is None:
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
    else:
        return connection


def reset_database(
    apps_to_migrate: list[str] = APPS_TO_MIGRATE,
    use_prebuilt: bool = False,
):
    # TODO: call_command("flush") could be used in the future to simply
    # delete all data -- without rerunning migrations

    # We can now proceed with reseting the database
    logging.info("Removing database and rebuilding...")

    # BUG: this is only for SQLite3 and Postgres
    # If I wish to add FULL functionality of all DBs, I could consider
    # wrapping the django-extensions function for this instead:
    #   https://django-extensions.readthedocs.io/en/latest/reset_db.html
    # An example command to call this (when django-extensions is installed) is...
    #   django-admin reset_db --settings=simmate.config.django.settings
    # Note: this does not remove migration files or reapply migrating after

    if settings.database_backend == "sqlite3":
        # grab the location of the database file. I assume the default
        # database for now.
        db_filename = Path(settings.database.name)

        # delete the sqlite3 database file if it exists
        if db_filename.exists():
            db_filename.unlink()

    elif settings.database_backend == "postgresql":
        # We do this with an independent postgress connection, rather than through
        # django so that we can close everything down easily.
        connection = postgres_connect_maintenance_db()

        # In order to delete a full database, we need to isolate this call
        connection.set_isolation_level(0)

        # Open connection cursor to perform database operations
        cursor = connection.cursor()

        # Build out database extensions and tables
        db_name = settings.database.name

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

    elif settings.database_backend not in ["postgresql", "sqlite3"]:
        logging.warning(
            "reseting your database is only supported for SQLite and Postgres."
            " Make sure you only use this function when initially building your "
            "database and not after."
        )

    # instead of building the database from scratch, we instead download a
    # prebuilt database file.
    if settings.database_backend == "sqlite3" and use_prebuilt:
        from simmate.database.utils import load_default_sqlite3_build

        logging.info("Setting up prebuilt database...")
        load_default_sqlite3_build()

        # now update the database based on the registered apps
        update_database(apps_to_migrate, show_logs=False)

    # Otherwise we make an empty database.
    # Because this is our first time building the database, we also want to
    # load the Spacegroup metadata for us to query Structures by.
    else:
        from simmate.database.mixins import Spacegroup

        logging.info("Building empty database...")
        update_database(apps_to_migrate, show_logs=False)

        logging.info("Loading default data...")
        Spacegroup.load_source_data()

    # Let the user know everything succeeded
    logging.info("Success! Your database has been reset. :sparkles:")


def dump_database_to_json(
    filename: str = "database_dump.json",
    exclude: list[str] = [],
):
    # BUG: https://stackoverflow.com/questions/67616945/
    # os.environ["PYTHONIOENCODING"] = "utf8"  # DOESNT WORK...
    # python -Xutf8 manage.py dumpdata > data.json  # WORKS!

    # Begin writing the database to the json file.
    logging.info("Writing all data to JSON...")

    # execute the following commands to write the database to a json file
    call_command("dumpdata", output=filename, exclude=exclude)

    # Let the user know everything succeeded
    logging.info(
        f"Success! You should now see the file {filename} with all of your data."
    )


def load_database_from_json(filename: str = "database_dump.json"):
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


def get_all_table_names() -> list[str]:
    """
    Returns a list of all database table names as they appear in the SQL db
    """
    return [m._meta.db_table for c in apps.get_app_configs() for m in c.get_models()]


def get_all_table_docs(extra_docs: dict = {}, include_empties: bool = True) -> dict:
    """
    Returns a diction of all django tables names and their corresponding documentation.
    This is give as a dictionary where the keys are the SQL table name and values
    are the details in markdown format.
    """

    # BUG: This util will miss separate ManyToMany tables

    # TODO: consider adding "if as_text else m.get_table_docs()" for when I'd
    # like to get things back as a dictionary instead of markdown.

    # For third-party models (such as allauth), there isn't a doc util set up,
    # so we provide predefined descriptions here.
    extra_docs_defaults = {}
    extra_docs.update(extra_docs_defaults)

    all_docs = {}
    for model in apps.get_models():
        table_name = model._meta.db_table

        if table_name in extra_docs.keys():
            all_docs[table_name] = extra_docs[table_name]

        elif not hasattr(model, "get_table_docs"):
            if include_empties:
                all_docs[table_name] = "( no docs available for this table )"

        else:
            all_docs[table_name] = model.show_table_docs(print_out=False)

    return all_docs


def get_table(table_name: str):  # returns subclass of DatabaseTable
    """
    Given a table name (e.g. "MaterialsProjectStructure") or a full import
    path of a table, this will load and return the corresponding table class.

    This is a wrapper around the `DatabaseTable.get_table` method. We make it
    available within the utils to match the pattern of the
    `worklfows.utils.get_workflow` utility that is commonly used elsewhere
    """

    # local import is required to prevent circular dep. This is also a higher
    # level util for users, so we establish db connection for them upfront
    from simmate.database import connect
    from simmate.database.core import DatabaseTable

    return DatabaseTable.get_table(table_name=table_name)


# BUG: This function isn't working as intended
# def graph_database(filename="database_graph.png"):
#     # using django-extensions, we want to make an image of all the available
#     # tables in our database as well as their relationships.
#     # This is the equivalent of running the following command:
#     #   django-admin graph_models -a -o image_of_models.png --settings=...
#     call_command("graph_models", output=filename, all_applications=True, layout="fdp")

# -----------------------------------------------------------------------------


def download_app_data(app_name: str, source: str = "direct", **kwargs):
    """
    Downloads all data for a given Simmate app & loads it into the Simmate database
    """
    # we import DatabaseTable inside the function to prevent circular imports
    from simmate.database.core.table import DatabaseTable

    # Check that the app is installed
    try:
        app_config = apps.get_app_config(app_name)
    except LookupError:
        logging.critical(f"Unknown app '{app_name}'. Failed to download data.")
        return

    logging.info(f"Loading data for the '{app_name}' app")

    # Get all models for the app
    models = list(app_config.get_models())

    # If the app config defines a load_order, we sort the models accordingly
    if hasattr(app_config, "load_order"):
        # we want to sort the models based on their __name__ matching the load_order list
        # Any models not in the list will be put at the end
        order = app_config.load_order
        models.sort(
            key=lambda m: order.index(m.__name__) if m.__name__ in order else 9999
        )

    found_any = False
    for model in models:
        # Check if it's a DatabaseTable
        if not issubclass(model, DatabaseTable):
            continue

        # check for load_source_data (is it overridden?)
        # we check the __func__ to see if it matches the base one
        has_load_source = (
            model.load_source_data.__func__
            is not DatabaseTable.load_source_data.__func__
        )
        # check for archive link
        has_archive = (
            hasattr(model, "remote_archive_link") and model.remote_archive_link
        )

        if not has_load_source and not has_archive:
            continue

        found_any = True

        # Decide which one to call based on `source` and availability
        if source == "direct":
            if has_load_source:
                logging.info(f"Loading {model.__name__} from direct source...")
                model.load_source_data(**kwargs)
            elif has_archive:
                logging.info(f"Loading {model.__name__} from remote archive...")
                model.load_remote_archive(**kwargs)
        elif source == "archive":
            if has_archive:
                logging.info(f"Loading {model.__name__} from remote archive...")
                model.load_remote_archive(**kwargs)
            elif has_load_source:
                logging.info(f"Loading {model.__name__} from direct source...")
                model.load_source_data(**kwargs)
        else:
            logging.error(f"Unknown source '{source}'. Use 'direct' or 'archive'.")
            return

    if not found_any:
        logging.info(f"'{app_name}' does not have any datasets to download. Exiting.")
        return

    logging.info(
        f"Success! Your database now contains all data associated with the '{app_name}' app."
    )


def load_default_sqlite3_build():
    """
    Loads a sqlite3 database archive that has all third-party data already
    populated in it.
    """
    # DEV NOTE: the prebuild filename is updated when new versions call for it.
    # Therefore, this value hardcoded specifically for each simmate version
    archive_filename = "prebuild-2026-04-04.zip"

    # Make sure the backend is using SQLite3 as this is the only allowed format
    assert settings.database.engine == "django.db.backends.sqlite3"

    # check if the prebuild directory exists, and create it if not
    archive_dir = get_directory(settings.config_directory / "sqlite-prebuilds")

    archive_filename_full = archive_dir / archive_filename

    # check if the archive has been downloaded before. If not, download!
    if not archive_filename_full.exists():
        remote_archive_link = f"https://archives.simmate.org/{archive_filename}"
        # Download the archive zip file from the URL to the current working dir
        logging.info("Downloading database file...")
        urllib.request.urlretrieve(remote_archive_link, archive_filename_full)
        logging.info("Done downloading.")
    else:
        logging.info(
            f"Found past download at {archive_filename_full}. Using archive as base."
        )

    logging.info("Unpacking prebuilt to active database...")
    # uncompress the zip file to archive directory
    shutil.unpack_archive(
        archive_filename_full,
        extract_dir=archive_dir,
    )

    # rename and move the sqlite file to be the new database
    db_filename_orig = archive_filename_full.with_suffix(".sqlite3")  # was .zip
    db_filename_new = settings.database.name
    shutil.move(db_filename_orig, db_filename_new)
    logging.info("Done unpacking.")


def start_postgres_docker(
    password: str = "postgres",
    port: int = 5432,
):
    """
    Sets up a Postgres database using the image
    informaticsmatters/rdkit-cartridge-debian:Release_2025_03_3
    and mounts the postgres data volume to the config directory database
    (e.g. ~/simmate/database) and exposes the port to localhost.
    """

    # Ensure the database directory exists
    db_volume = get_directory(settings.config_directory / "database")

    # Define the docker command
    docker_command = [
        "docker",
        "run",
        "--name",
        "simmate_db",
        "-d",
        "-p",
        f"{port}:5432",
        "-v",
        f"{db_volume}:/var/lib/postgresql/data",
        "-e",
        f"POSTGRES_PASSWORD={password}",
        "informaticsmatters/rdkit-cartridge-debian:Release_2025_03_3",
    ]

    # execute the command
    logging.info("Starting Postgres container via Docker...")
    subprocess.run(docker_command, check=True)
    logging.info("Success! Container 'simmate_db' is running.")

    # check the current settings and update if they don't match
    new_db_settings = {
        "engine": "django.db.backends.postgresql",
        "host": "localhost",
        "port": port,
        "name": "simmate_local_dev",  # fixed to deter misuse of dev setup
        "user": "postgres",
        "password": password,
    }
    if settings.database != new_db_settings:
        logging.info("Updating Simmate settings to use this database...")
        settings.write_updated_settings({"database": new_db_settings})


def stop_postgres_docker():
    """
    Stops and removes the Postgres container 'simmate_db'
    """

    # Define the docker commands
    stop_command = ["docker", "stop", "simmate_db"]
    remove_command = ["docker", "rm", "simmate_db"]

    # execute the commands
    logging.info("Stopping and removing Postgres container via Docker...")
    try:
        subprocess.run(stop_command, check=True, capture_output=True)
        subprocess.run(remove_command, check=True, capture_output=True)
        logging.info("Success! Container 'simmate_db' has been stopped and removed.")
    except subprocess.CalledProcessError as error:
        logging.error(f"Failed to stop/remove container: {error.stderr.decode()}")


def create_prebuild():
    """
    Creates a date-stamped zip file of the current SQLite3 database.
    The zip file is saved in the `<config dir>/sqlite-prebuilds/` directory.
    """

    if settings.database_backend != "sqlite3":
        raise Exception("create_prebuild is only supported for SQLite3")

    current_date = datetime.now().strftime("%Y-%m-%d")
    prebuild_name = f"prebuild-{current_date}"
    db_filename = Path(settings.database.name)

    if not db_filename.exists():
        raise FileNotFoundError(f"Database file not found: {db_filename}")
    archive_dir = get_directory(settings.config_directory / "sqlite-prebuilds")
    zip_filename = archive_dir / f"{prebuild_name}.zip"

    logging.info(f"Creating prebuild archive at {zip_filename}...")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(db_filename, arcname=f"{prebuild_name}.sqlite3")

    logging.info(f"Success! Prebuild created: {zip_filename.name}")
