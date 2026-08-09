# -*- coding: utf-8 -*-


import shutil
from pathlib import Path

import streamlit


def patch_streamlit_index_html():
    """
    Replaces streamlit's `index.html` static file with a custom simmate one.

    The custom one includes JS for rendering molecules using RDkit.js
    """

    # This is the default index for streamlit, where they don't give us an option
    # to override it. We therefore "hack" streamlit by replacing its static file
    # with one of our custom ones.
    # https://github.com/streamlit/streamlit/blob/develop/frontend/app/index.html
    index_original = Path(streamlit.__file__).parent / "static" / "index.html"
    assert index_original.exists()

    # copy to placeholder file just in case we ever need to revert
    index_original_backup = index_original.parent / "index_backup.html"
    shutil.copy(src=index_original, dst=index_original_backup)

    # grab the patched file and place it at the index.html
    index_patched = (
        Path(__file__).parent
        / "templates"
        / "analysis_dashboard"
        / "streamlit_index_patched.html"
    )
    assert index_patched.exists()
    shutil.copy(src=index_patched, dst=index_original)


def unpatch_streamlit_index_html():
    """
    uses the backup from `patch_streamlit_index_html` to restore the default
    index.html file
    """
    index_original = Path(streamlit.__file__).parent / "static" / "index.html"
    index_original_backup = index_original.parent / "index_backup.html"
    assert index_original_backup.exists()
    shutil.copy(src=index_original_backup, dst=index_original)
