# -*- coding: utf-8 -*-

import os
import shutil

from django.apps import apps
from django.core.management import call_command

from simmate.configuration.django.settings import DATABASES

# Lists off which apps to update/create. By default, I do all apps that are installed
# so this list is grabbed directly from django. I also grab the CUSTOM_APPS to
# check for user-installed applications.
APPS_TO_MIGRATE = list(apps.app_configs.keys())


def update_database(apps_to_migrate=APPS_TO_MIGRATE):

    # execute the following commands to update the database
    call_command("makemigrations", *apps_to_migrate)
    call_command("migrate")


def reset_database(apps_to_migrate=APPS_TO_MIGRATE, use_prebuilt=False):

    # BUG: Why doesn't call_command("flush") do this? How is it different?

    # BUG: this is only for SQLite3
    # Consider wrapping the django-extensions function for this instead:
    #   https://django-extensions.readthedocs.io/en/latest/reset_db.html
    # An example command to call this (when django-extensions is installed) is...
    #   django-admin reset_db --settings=simmate.configuration.django.settings
    # Note: this does not remove migration files or reapply migrating after
    # Make sure the backend is using SQLite3 as this is the only allowed format
    using_sqlite = DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    if not using_sqlite:
        print(
            "WARNING: reseting your database does not clear your database tables "
            "for non-sqlite3 backends. Make sure you only use this function when "
            "initially building your database and not after."
        )

    # grab the location of the database file. I assume the default database for now.
    db_filename = DATABASES["default"]["NAME"]

    # delete the sqlite3 database file if it exists
    if os.path.exists(db_filename):
        os.remove(db_filename)

    # go through each app directory and delete all folders named 'migrations'
    for app_name, app_config in apps.app_configs.items():

        # Skip if the app was not requested
        if app_config.label not in apps_to_migrate:
            continue

        migration_dir = os.path.join(app_config.path, "migrations")
        if os.path.exists(migration_dir):
            shutil.rmtree(migration_dir)
            continue

    # now update the database based on the registered models
    update_database(apps_to_migrate)

    # instead of building the database from scratch, we instead download a
    # prebuilt database file.
    if using_sqlite and use_prebuilt:
        from simmate.database.third_parties import load_default_sqlite3_build

        load_default_sqlite3_build()

    # Otherwise we leave the empty database.
    # Because this is our first time building the database, we also want to
    # load the Spacegroup metadata for us to query Structures by.
    else:
        from simmate.database.base_data_types import Spacegroup

        Spacegroup._load_database_from_toolkit()


def dump_database_to_json(filename="database_dump.json", exclude=[]):

    # execute the following commands to write the database to a json file
    call_command("dumpdata", output=filename, exclude=exclude)


def load_database_from_json(filename="database_dump.json"):

    # OPTIMIZE: this function is very slow. Consider speed-up options such as
    # making this function a transaction or manually writing a bulk_create. It
    # actually looks like django ORM takes up most of the time tough, and the actual
    # database queries are not the bottleneck...

    # execute the following commands to build the database
    # BUG: contenttypes gives issues because a migrated database already has these
    # set. Simply ignore this table and everything works. The contenttypes is
    # simply a table that lists all of our different models.
    call_command("loaddata", filename, exclude=["contenttypes"])


# BUG: This function isn't working as intended
# def graph_database(filename="database_graph.png"):

#     # using django-extensions, we want to make an image of all the available
#     # tables in our database as well as their relationships.

#     # This is the equivalent of running the following command:
#     #   django-admin graph_models -a -o image_of_models.png --settings=...
#     call_command("graph_models", output=filename, all_applications=True, layout="fdp")
