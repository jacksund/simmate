# -*- coding: utf-8 -*-

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


def connect_database_only():  # Wall time: 200 ms first call and 600 ns after

    # see if django has already been configured. If so, just exit this function.
    if settings.configured:
        return

    # import the settings I want from the actual django settings file
    from simmate.configuration.django.settings import BASE_DIR, DATABASES, DEBUG

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


# upon import of this module, I run the setup immediately so the user doesn't have to
connect_database_only()
