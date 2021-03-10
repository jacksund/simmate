# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

import os
import sys

import django
from django.conf import settings

# BUG: import the settings raises an error in spyder. Should I moving this import
# inside of the setup_django_full() function?

# --------------------------------------------------------------------------------------

# NOTE -- connecting just the Django database ORM has only a 0.05 second advantage
# on the initial import and then only 1.8e-7 second advantage after. Based on
# that, there really isn't much to gain from running the reduced setup. Even
# in ETL methods, I believe the bottleneck will still be the internet connection
# and not the django_setup. Having users always setup all of django can solve
# a lot of potential headaches at roughly the same speed.


def setup_full():  # Wall time: 250 ms first call and 175 ns after

    # OPTIMIZE: this function will take longer than 250ms when other imports
    # get involved. For example, simmate.database.diffusion has some pymatgen
    # imports that that >0.8s and make this function take over 1s. I should have
    # setup_select() function that only configures "select" apps to help with
    # setup speed.

    # see if django has already been configured. If so, just exit this function.
    # BUG: originally I used the code below, but it didn't work with Prefect+Dask:
    #   if "DJANGO_SETTINGS_MODULE" in os.environ:
    if settings.configured:
        return

    # The code below is the equiv of running 'python manage.py shell'
    # This sets up all of django for its full use. You can being importing
    # models after this is setup.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "simmate.configuration.django.settings"
    )
    django.setup()

    # SECURITY WARNING: I added this setting myself! delete when in production
    # BUG: I believe this is just for use within Spyder and Jupyter, which I think
    # are examples of async enviornments. In production (non-dev), I believe I should
    # turn this off though.
    # !!! REMOVE IN PRODUCTION
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


def connect_database_only():  # Wall time: 200 ms first call and 600 ns after

    # see if django has already been configured. If so, just exit this function.
    if settings.configured:
        return

    # import the settings I want from the actual django settings file
    from simmate.website.core.settings import BASE_DIR, DATABASES, DEBUG

    # For speed, I only want this app installed
    # I also need to write out the full import path from django here.
    INSTALLED_APPS = ("simmate.website.diffusion.apps.DiffusionConfig",)
    # set these values

    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=DEBUG,
        DATABASES=DATABASES,
        INSTALLED_APPS=INSTALLED_APPS,
    )
    django.setup()


def setup_django_cli():  # TODO -- move this to the command_line module
    # This is if you call the file directory from the command line interface (cli)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "simmate.website.core.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


# --------------------------------------------------------------------------------------


def runserver():

    # for now I recommend using the shell command...
    #   "django-admin runserver --setting=simmate.settings"
    # or... navigate to the directory and use
    #   "python manage.py runserver"
    raise NotImplementedError

    # BUG: I'm not sure why this code below doesn't work...
    # execute the following command to run the server
    # from django.core.management import call_command
    # call_command('runserver')

    # BUG: this code sorta works... but I'm not able to kill the server once
    # it's launched - even with .terminate() and restarting spyder
    #
    # grab the working directory
    # wait=False, timeout=300
    # from puttyexams.settings import BASE_DIR
    # from subprocess import Popen
    # # and now submit the command via a separate shell
    # future = Popen(
    #     "python manage.py runserver",
    #     cwd=BASE_DIR,
    #     shell=True,
    # )
    # # see if we want to wait until the command completes or not
    # if wait:
    #     future.wait(timeout=timeout)
    #     # kill the task after the timeout
    #     future.terminate()
    # # return the future if the user wants it
    # return future


# --------------------------------------------------------------------------------------

# TODO -- move this to the commandline module
# if __name__ == "__main__":
#     setup_django_cli()
