# -*- coding: utf-8 -*-

import base64
import csv
import io
import json
import logging
import shutil
import subprocess
import urllib
import zipfile
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

import polars
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.color import no_style
from django.db import connection, models, transaction
from django.db.utils import DatabaseError
from django.utils import timezone

from simmate.config import settings
from simmate.utils import get_directory

# Lists off which apps to update/create. By default, I do all apps that are installed
# so this list is grabbed directly from django. I also grab the CUSTOM_APPS to
# check for user-installed applications.
APPS_TO_MIGRATE = list(apps.app_configs.keys())


def batch_bulk_create(
    batch_size: int = 1000,
    update_conflicts: bool = False,
    unique_fields: list[str] = None,
    update_fields: list[str] = None,
):
    """
    Decorator for the `load_source_data` classmethod on DatabaseTables.
    Expects the wrapped method to be a generator that yields database objects.
    This handles creating the objects in batches using `bulk_create`.

    By default, conflicts are ignored (insert-only). To enable upsert behavior,
    set `update_conflicts=True` and provide `unique_fields` and `update_fields`.
    """

    if update_conflicts:
        bulk_create_kwargs = dict(
            update_conflicts=True,
            unique_fields=unique_fields,
            update_fields=update_fields,
        )
    else:
        bulk_create_kwargs = dict(ignore_conflicts=True)

    def decorator(func):
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            db_objs = []
            for obj in func(cls, *args, **kwargs):
                if obj is None:
                    continue
                db_objs.append(obj)
                if len(db_objs) >= batch_size:
                    cls.objects.bulk_create(
                        db_objs,
                        batch_size=batch_size,
                        **bulk_create_kwargs,
                    )
                    db_objs = []  # reset for next batch
            # save any remaining
            if db_objs:
                cls.objects.bulk_create(
                    db_objs,
                    batch_size=batch_size,
                    **bulk_create_kwargs,
                )

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

        if "simmate.apps.configs.ProjectManagementConfig" in settings.apps:
            from simmate.apps.project_management.models import Wallet

            Wallet.load_source_data()

    # Let the user know everything succeeded
    logging.info("Success! Your database has been reset. :sparkles:")


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
                model.load_source_data(**kwargs)
            elif has_archive:
                model.load_remote_archive(**kwargs)
        elif source == "archive":
            if has_archive:
                model.load_remote_archive(**kwargs)
            elif has_load_source:
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
        remote_archive_link = f"https://assets.simmate.org/{archive_filename}"
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
    docker.io/informaticsmatters/rdkit-cartridge-debian:Release_2025_03_3
    and mounts the postgres data volume to the config directory database
    (e.g. ~/simmate/database) and exposes the port to localhost.
    """

    # Ensure the database directory exists
    db_volume = get_directory(settings.config_directory / "database")

    # Check if the container already exists
    check_command = ["docker", "container", "inspect", "simmate_db"]
    result = subprocess.run(check_command, capture_output=True)

    if result.returncode == 0:
        # Container exists, just start it
        logging.info("Container 'simmate_db' already exists. Restarting...")
        start_command = ["docker", "start", "simmate_db"]
        subprocess.run(start_command, check=True)
        logging.info("Success! Container 'simmate_db' is running.")
    else:
        # Define the docker command to create and run a new container
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
            "docker.io/informaticsmatters/rdkit-cartridge-debian:Release_2025_03_3",
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
    Stops the Postgres container 'simmate_db'
    """

    # Define the docker commands
    stop_command = ["docker", "stop", "simmate_db"]

    # execute the commands
    logging.info("Stopping Postgres container via Docker...")
    try:
        subprocess.run(stop_command, check=True, capture_output=True)
        logging.info("Success! Container 'simmate_db' has been stopped.")
    except subprocess.CalledProcessError as error:
        logging.error(f"Failed to stop container: {error.stderr.decode()}")


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


def get_fake_data_path(app_label: str) -> Path:
    """
    Returns the path to an app's fake data archive (`test/fake_data.zip`
    within the app's folder). The file may not exist.
    """
    return Path(apps.get_app_config(app_label).path) / "test" / "fake_data.zip"


FAKE_USERNAMES = [
    "chemist1",
    "chemist2",
    "chemist3",
    "chemist4",
    "lab_manager",
    "technician",
]
"""
Users shared by all apps' fake data. Users are matched by username when
loaded, so every app can include these and they are only created once.
"""


def get_fake_users() -> list[dict]:
    """
    Gives `auth.User` rows for `FAKE_USERNAMES`, for use with `write_fake_data`.
    Their ids are 1, 2, 3... in the order of `FAKE_USERNAMES`.
    """
    return [
        dict(
            id=i,
            username=username,
            email=f"{username}@example.com",
            password="!",  # unusable password
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        for i, username in enumerate(FAKE_USERNAMES, start=1)
    ]


def write_fake_data(
    filename: Path,
    tables: dict[str, list[dict]],
    reference_date: datetime,
):
    """
    Writes fake data in the format that `load_fake_data` reads.

    #### Parameters

    - `filename`:
        The zip file to write (typically `get_fake_data_path(app_label)`)
    - `tables`:
        Rows for each model label (e.g. "inventory_management.Batch"), given
        in the order they should be loaded. Columns should be the database
        column names (e.g. `batch_id`). Datetimes, bytes, and lists/dicts
        (for JSON columns) are converted for you.
    - `reference_date`:
        The date the data was generated at. This becomes "now" when loaded.
    """
    with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "metadata.json",
            json.dumps({"reference_date": reference_date.isoformat()}),
        )
        for i, (label, rows) in enumerate(tables.items(), start=1):
            buffer = io.StringIO()
            writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: _to_csv_value(v) for k, v in row.items()})
            archive.writestr(f"{i:02d}_{label}.csv", buffer.getvalue())
            logging.info(f"Wrote {len(rows):,} rows for {label}")


def _to_csv_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode()  # read by BinaryField.to_python
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def load_fake_data(app_label: str) -> dict[str, int]:
    """
    Loads an app's fake data (`test/fake_data.zip`, made by `write_fake_data`)
    into the database. This is meant for tests and for populating a fresh dev
    database, so that UIs can be explored without real data.

    The zip contains a `metadata.json` and one CSV per table:

    - `metadata.json` gives the `reference_date` that the data was generated
      at. All datetime columns are shifted by `now - reference_date` so that
      relative dates (e.g. "expires in 10 days") stay the same over time.
    - CSVs are named `NN_<app_label>.<ModelName>.csv`, where `NN` sets the
      load order (so foreign keys exist before they are referenced). Columns
      use the column names in the database (e.g. `batch_id`) and include
      explicit `id`s. Many-to-many links use the auto-generated through model
      (e.g. `inventory_management.Batch_parent_batches.csv`).

    Rows of a `DatabaseTable` are built with `from_toolkit`, so toolkit
    columns (e.g. a `molecule` given as SMILES) get fully populated.

    Users are matched by username, so they can be shared across apps and real
    users are left alone. All other tables use explicit IDs, so this will
    fail if any of the rows already exist. Load into an empty database (e.g.
    after `simmate database reset`).

    #### Parameters

    - `app_label`:
        The label of the app to load data for (e.g. "inventory_management")

    #### Returns

    The number of rows loaded for each table
    """
    from simmate.database.core import DatabaseTable

    filename = get_fake_data_path(app_label)
    if not filename.exists():
        raise FileNotFoundError(f"No fake data found for the '{app_label}' app")

    with zipfile.ZipFile(filename) as archive:
        metadata = json.loads(archive.read("metadata.json"))
        tables = {
            name: archive.read(name)
            for name in sorted(archive.namelist())
            if name.endswith(".csv")
        }

    reference_date = datetime.fromisoformat(metadata["reference_date"])
    date_shift = timezone.now() - reference_date

    user_model = get_user_model()
    user_ids = {}  # fake user id --> real user id
    loaded_models = []
    counts = {}
    with transaction.atomic():
        for name, content in tables.items():
            label = name.split("_", 1)[1].removesuffix(".csv")
            model = apps.get_model(label)
            df = polars.read_csv(io.BytesIO(content), infer_schema=False)
            parsers = _get_fake_data_parsers(model, df.columns, date_shift, user_ids)
            entries = [
                {
                    column: parsers[column](value) if value else None
                    for column, value in row.items()
                }
                for row in df.to_dicts()
            ]
            counts[label] = len(entries)

            # users are shared across apps (and real ones may already exist),
            # so we match on username and remap their ids in other tables
            if model == user_model:
                for entry in entries:
                    fake_id = entry.pop("id")
                    user, _ = user_model.objects.get_or_create(
                        username=entry.pop("username"),
                        defaults=entry,
                    )
                    user_ids[fake_id] = user.id
                continue

            if issubclass(model, DatabaseTable):
                objs = [model.from_toolkit(**entry) for entry in entries]
            else:
                objs = [model(**entry) for entry in entries]
            model.objects.bulk_create(objs)
            loaded_models.append(model)

            # auto_now(_add) columns are overwritten on create, so we restore
            # the original timestamps (bulk_update skips auto_now)
            auto_columns = [
                field.attname
                for field in model._meta.concrete_fields
                if field.attname in df.columns
                and (
                    getattr(field, "auto_now", False)
                    or getattr(field, "auto_now_add", False)
                )
            ]
            if auto_columns:
                for obj, entry in zip(objs, entries):
                    for column in auto_columns:
                        setattr(obj, column, entry[column])
                model.objects.bulk_update(objs, auto_columns)

            logging.info(f"Loaded {len(objs):,} rows into {label}")

        # explicit ids don't advance the auto-increment sequences (Postgres)
        sql = connection.ops.sequence_reset_sql(no_style(), loaded_models)
        with connection.cursor() as cursor:
            for statement in sql:
                cursor.execute(statement)

    return counts


def _get_fake_data_parsers(
    model,
    columns: list[str],
    date_shift: timedelta,
    user_ids: dict[int, int],
) -> dict[str, callable]:
    """
    Gives a function for each CSV column that converts its string values into
    python values for the given model.
    """
    fields = {field.attname: field for field in model._meta.concrete_fields}
    parsers = {}
    for column in columns:
        field = fields[column]
        if isinstance(field, models.ForeignKey):
            if field.related_model == get_user_model():
                parsers[column] = lambda v: user_ids[int(v)]
                continue
            field = field.target_field
        if isinstance(field, models.JSONField):
            parsers[column] = json.loads
        elif isinstance(field, models.DateTimeField):
            parsers[column] = lambda v, f=field: f.to_python(v) + date_shift
        else:
            parsers[column] = field.to_python
    return parsers
