# -*- coding: utf-8 -*-

import logging
import os
import shutil
import zipfile
from pathlib import Path

import requests

from simmate.config import settings


def download_ketcher():
    """
    Downloads and extracts the Ketcher standalone zip to the static directory.
    This is required to avoid CORS issues when accessing the Ketcher API
    from an iframe.
    """

    ketcher_url = "https://github.com/epam/ketcher/releases/download/v3.12.0/ketcher-standalone-3.12.0.zip"

    # We download to the user's config directory instead of the source tree.
    # This directory is already in Django's STATICFILES_DIRS.
    static_dir = settings.config_directory / "static_files" / "ketcher"

    if (static_dir / "index.html").exists():
        return

    logging.info("Downloading Ketcher...")

    # ensure directory exists and is empty
    if static_dir.exists():
        shutil.rmtree(static_dir)
    os.makedirs(static_dir, exist_ok=True)

    zip_path = static_dir.parent / "ketcher.zip"

    response = requests.get(ketcher_url, stream=True)
    if response.status_code == 200:
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        logging.error(f"Failed to download Ketcher (status {response.status_code})")
        return

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # The zip contains a 'standalone' folder, we want the contents of that folder
        # directly in our static_dir.
        for member in zip_ref.namelist():
            if member.startswith("standalone/"):
                # strip the 'standalone/' prefix
                filename = member[len("standalone/") :]
                if not filename:
                    continue

                target_path = static_dir / filename
                if member.endswith("/"):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    # ensure parent dir exists
                    os.makedirs(target_path.parent, exist_ok=True)
                    with (
                        zip_ref.open(member) as source,
                        open(target_path, "wb") as target,
                    ):
                        shutil.copyfileobj(source, target)

    os.remove(zip_path)
    logging.info("Ketcher installation complete.")
