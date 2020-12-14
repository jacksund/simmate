# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import os
import shutil
import sys
import django

# --------------------------------------------------------------------------------------


def setup_django_full(): # Wall time: 246 ms
    
    # The code below is the equiv of running 'python manage.py shell'
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fhahtda.website.core.settings")
    django.setup()


def connect_db(): # Wall time: 200 ms first time and 600 ns after
    
    # see if django has already been configured. If so, just exit this function
    from django.conf import settings
    if settings.configured:
        return 
    
    # import the settings I want from the actual django settings file
    from fhahtda.website.core.settings import BASE_DIR, DATABASES, DEBUG

    # For speed, I only want this app installed
    # I also need to write out the full import path from django here.
    INSTALLED_APPS = ("fhahtda.website.diffusion.apps.DiffusionConfig",)
    # set these values
    
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=DEBUG,
        DATABASES=DATABASES,
        INSTALLED_APPS=INSTALLED_APPS,
    )
    django.setup()


def setup_django_cli():
    # This is if you call the file directory from the command line interface (cli)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fhahtda.website.core.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


# --------------------------------------------------------------------------------------


def reset_db(apps_to_migrate=["diffusion"]):
    # Apps to init.
    #!!! In the future, I should do a more robust search, rather than hardcode here.
    #!!! maybe just grab all folders in the base directory via os.listdir()?

    # grab base directory and the location of the database file
    from fhahtda.website.core.settings import BASE_DIR, DATABASES

    db_filename = DATABASES["default"]["NAME"]

    # delete the sqlite3 database file if it exists
    if os.path.exists(db_filename):
        os.remove(db_filename)

    # go through each listed directory in the base directory
    # and delete all folders named 'migrations'
    for app in apps_to_migrate:
        migration_dir = os.path.join(BASE_DIR, app, "migrations")
        if os.path.exists(migration_dir):
            shutil.rmtree(migration_dir)

    # setup django before we call any commands
    setup_django_full()

    # execute the following commands to build the database
    from django.core.management import call_command

    call_command("makemigrations", *apps_to_migrate)
    call_command("migrate")


# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    setup_django_cli()
