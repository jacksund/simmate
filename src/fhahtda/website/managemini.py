# -*- coding: utf-8 -*-

# This file sets up and configures Django when we are only using the ORM

import django
from django.conf import settings

# import the settings I want from the actual django settings file
from fhahtda.website.core.settings import BASE_DIR, DATABASES, DEBUG
# For speed, I only want this app installed
# I also need to write out the full import path from django here.
INSTALLED_APPS = ('fhahtda.website.diffusion.apps.DiffusionConfig',)
# INSTALLED_APPS = ('diffusion.apps.DiffusionConfig',)

def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=DEBUG,
        DATABASES=DATABASES,
        INSTALLED_APPS=INSTALLED_APPS,
    )
    django.setup()
