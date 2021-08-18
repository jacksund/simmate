# -*- coding: utf-8 -*-

import os
import shutil

from django.core.management import call_command

from simmate.configuration.django import setup_full  # sets database connection
from simmate.configuration.django.settings import DJANGO_DIRECTORY, DATABASES
from simmate.database.symmetry import Spacegroup


def update_database(apps_to_migrate=["local_calculations", "third_parties"]):

    # execute the following commands to update the database
    call_command("makemigrations", *apps_to_migrate)
    call_command("migrate")


def reset_database(apps_to_migrate=["local_calculations", "third_parties"]):
    # BUG: this is only for SQLite3

    # Apps to init.
    # !!! In the future, I should do a more robust search, rather than hardcode here.
    # !!! maybe just grab all folders in the base directory via os.listdir()?

    # BUG: Why doesn't call_command("flush") do this? How is it different?

    # grab the location of the database file. I assume the default database for now.
    db_filename = DATABASES["default"]["NAME"]

    # delete the sqlite3 database file if it exists
    if os.path.exists(db_filename):
        os.remove(db_filename)

    # go through each listed directory in the base directory
    # and delete all folders named 'migrations'
    for app in apps_to_migrate:
        migration_dir = os.path.join(DJANGO_DIRECTORY, app, "migrations")
        if os.path.exists(migration_dir):
            shutil.rmtree(migration_dir)

    # now update the database based on the registered models
    update_database(apps_to_migrate)

    # because this is our first time building the database, we also want to
    # load the Spacegroup metadata for us to query Structures by.
    Spacegroup.load_database_from_pymatgen()


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
