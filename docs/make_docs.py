# -*- coding: utf-8 -*-

# This file generates our html documentation using pdoc.

from pathlib import Path

import pdoc

if __name__ == "__main__":

    # We must load Django settings first -- otherwise model imports will raise errors
    from simmate.configuration.django import setup_full  # sets up Django

    # Set our default settings for the pdoc command
    pdoc.render.configure(
        docformat=None,  # uses markdown (the default)
        edit_url_map={
            "simmate": "https://github.com/jacksund/simmate/tree/main/src/simmate/"
        },
        footer_text="",
        logo="https://github.com/jacksund/simmate/blob/main/logo/simmate.svg?raw=true",
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
