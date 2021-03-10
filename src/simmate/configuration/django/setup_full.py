# -*- coding: utf-8 -*-

import os

import django
from django.conf import settings

# BUG: import the settings raises an error in spyder. Should I moving this import
# inside of the setup_django_full() function?

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


# When I import this module, it automatically configures django for us, including
# connecting to the database(s). Without this file, I would instead need these two
#  lines in every single file before I import models:
#   from simmate.configuration.django import setup_full
#   setup_full() # ensures setup
# With this init, I instead only need to have one line:
#   from simmate.configuration.django import setup_full # ensures setup
# Thus this "module" is more of a script.
setup_full()
