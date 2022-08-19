# -*- coding: utf-8 -*-

"""
This file is for running Django's configuration commands. While Simmate
makes these commands available through the django-admin command, we still
include this file because DigitalOcean uses it for their App Platform.
Beginners can just ignore this file.
"""

import os
import sys

if __name__ == "__main__":

    # We set an enviornment variable that tells django where our site in installed
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "simmate.configuration.django.settings"
    )

    # Now that our settings our configured, we take whatever command was used
    # in the commandline and call it.
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
