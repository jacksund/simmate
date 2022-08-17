# -*- coding: utf-8 -*-

import logging
import shutil
import urllib

from simmate.configuration.django.settings import DATABASES, SIMMATE_DIRECTORY
from simmate.database.third_parties import AflowPrototype  # AflowStructure,
from simmate.database.third_parties import (
    CodStructure,
    JarvisStructure,
    MatprojStructure,
    OqmdStructure,
)
from simmate.utilities import get_directory


def load_remote_archives(**kwargs):
    """
    Goes through all third-party databases and loads their most recent remote
    archives (if available). This utility helps with initializing a new
    database build.

    Accepts the same parameters as the `load_remote_archive` method

    WARNING:
    This can take several hours to run and there is no pause/continuation
    implemented. This runs substantially faster when you are using a cloud
    database backend (e.g. Postgres) and use `parallel=True`.

    If you are using SQLite, we highly recommend using `load_default_sqlite3_build`
    instead of this utility, which downloads a full database that was built using
    this method.
    """

    logging.info("Loading AFLOW Prototypes")
    AflowPrototype.load_remote_archive(**kwargs)

    logging.info("Loading JARVIS data")
    JarvisStructure.load_remote_archive(**kwargs)

    logging.info("Loading MatProj data")
    MatprojStructure.load_remote_archive(**kwargs)

    logging.info("Loading OQMD data")
    OqmdStructure.load_remote_archive(**kwargs)

    logging.info("Loading COD data")
    CodStructure.load_remote_archive(**kwargs)  # BUG: this crashes the IDE.


def load_default_sqlite3_build():
    """
    Loads a sqlite3 database archive that has all third-party data already
    populated in it.
    """
    # DEV NOTE: the prebuild filename is updated when new versions call for it.
    # Therefore, this value hardcoded specifically for each simmate version
    archive_filename = "prebuild-2022-08-17.zip"

    # Make sure the backend is using SQLite3 as this is the only allowed format
    assert DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

    # check if the prebuild directory exists, and create it if not
    archive_dir = get_directory(SIMMATE_DIRECTORY / "sqlite-prebuilds")

    archive_filename_full = archive_dir / archive_filename

    # check if the archive has been downloaded before. If not, download!
    if not archive_filename_full.exists():
        remote_archive_link = f"https://archives.simmate.org/{archive_filename}"
        # Download the archive zip file from the URL to the current working dir
        logging.info("Downloading database file...")
        urllib.request.urlretrieve(remote_archive_link, archive_filename_full)
        logging.info("Done downloading.")
    else:
        logging.info(
            f"Found past download at {archive_filename_full}. Using archive as base."
        )

    logging.info("Unpacking prebuilt to active database...")
    # uncompress the zip file to archive directory
    shutil.unpack_archive(
        archive_filename_full,
        extract_dir=archive_dir,
    )

    # rename and move the sqlite file to be the new database
    db_filename_orig = archive_filename_full.with_suffix(".sqlite3")  # was .zip
    db_filename_new = DATABASES["default"]["NAME"]
    shutil.move(db_filename_orig, db_filename_new)
    logging.info("Done unpacking.")
