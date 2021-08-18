# -*- coding: utf-8 -*-

import os
import sys

# TODO: move this functionality to the command_line module


def setup_django_cli():
    # This is if you call the file directory from the command line interface (cli)
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "simmate.configuration.django.settings"
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    setup_django_cli()
