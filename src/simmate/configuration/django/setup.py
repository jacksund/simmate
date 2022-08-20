# -*- coding: utf-8 -*-

import logging
import os

import django
from django.conf import settings

from simmate.utilities import check_if_using_latest_version


def setup_django():
    """
    Configures django settings. This method does not need to be called directly
    because importing this module does so automatically.

    The first time this function is used can take >1 seconds because many things
    are imported from the start. Thereafter, testing shows that only <200 ns
    are used when settings are already configured.
    """

    # OPTIMIZE: I should have setup_select() function that only configures
    # "select" apps to help with setup speed.

    # see if django has already been configured. If so, just exit this function.
    if settings.configured:
        return
    # BUG: originally I used the code below, but it didn't work with Prefect+Dask:
    #   if "DJANGO_SETTINGS_MODULE" in os.environ:

    # Check if there is a newer Simmate version available, and if the current
    # installation is out of date, print a message for the user.
    try:
        check_if_using_latest_version()
    except:
        logging.warning("Unable to check if using the latest Simmate version.")

    logging.info("Configuring database and workflows :hammer_and_wrench:")
    # The code below is the equiv of running 'python manage.py shell'
    # This sets up all of django for its full use. You can being importing
    # models after this is setup.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "simmate.configuration.django.settings"
    )
    django.setup()
    logging.info("Configuration complete :rocket:")


# When I import this module, it automatically configures django for us, including
# connecting to the database(s). Without this file, I would instead need these two
#  lines in every single file before I import models:
#   from simmate.configuration.django import setup
#   setup_django() # ensures setup
# With this init, I instead only need to have one line:
#   from simmate.configuration.django import setup
# Thus this "module" is more of a script.
setup_django()
