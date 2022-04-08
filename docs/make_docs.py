# -*- coding: utf-8 -*-

"""
This file generates our html documentation using pdoc.

This does not need to be called directly because this script is automatically
ran by the `.github/workflows/make-docs.yml` workflow every time a Simmate
release is made. The exception to this is if you'd like to host documentation
locally for offline-access.
"""

import os
from pathlib import Path

import pdoc

import django

if __name__ == "__main__":

    # We must load Django settings first -- otherwise model imports will raise errors
    #   from simmate.configuration.django import setup_full  # sets up Django
    # Normally we'd use the line above this, but we want to include the test
    # database tables too, so we modify that here.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "simmate.configuration.django.settings_test"
    )
    django.setup()
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

    # Set our default settings for the pdoc command
    pdoc.render.configure(
        docformat=None,  # uses markdown (the default)
        edit_url_map={
            "simmate": "https://github.com/jacksund/simmate/tree/main/src/simmate/"
        },
        footer_text="",
        logo="https://github.com/jacksund/simmate/blob/main/src/simmate/website/static_files/images/simmate-logo.svg?raw=true",
        logo_link="https://github.com/jacksund/simmate",
        math=False,
        search=True,
        show_source=True,
        template_directory=None,
    )

    # Now generate all documentation
    all_docs = pdoc.pdoc(
        "../src/simmate",
        output_directory=Path("."),
        format="html",
    )
