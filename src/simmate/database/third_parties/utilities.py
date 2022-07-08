# -*- coding: utf-8 -*-

import os
import urllib
import shutil

from simmate.utilities import get_directory
from simmate.configuration.django.settings import DATABASES, SIMMATE_DIRECTORY
from simmate.database.third_parties import (
    # AflowStructure,
    AflowPrototype,
    CodStructure,
    JarvisStructure,
    MatprojStructure,
    OqmdStructure,
)


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

    AflowPrototype.load_remote_archive(**kwargs)
    CodStructure.load_remote_archive(**kwargs)
    JarvisStructure.load_remote_archive(**kwargs)
    MatprojStructure.load_remote_archive(**kwargs)
    OqmdStructure.load_remote_archive(**kwargs)


def load_default_sqlite3_build():
    """
    Loads a sqlite3 database archive that has all third-party data already
    populated in it.
    """
    # DEV NOTE: the prebuild filename is updated when new versions call for it.
    # Therefore, this value hardcoded specifically for each simmate version
    archive_filename = "prebuild-2022-07-05.zip"

    # Make sure the backend is using SQLite3 as this is the only allowed format
    assert DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"

    # check if the prebuild directory exists, and create it if not
    archive_dir = get_directory(os.path.join(SIMMATE_DIRECTORY, "sqlite-prebuilds"))

    archive_filename_full = os.path.join(archive_dir, archive_filename)

    # check if the archive has been downloaded before. If not, download!
    if not os.path.exists(archive_filename_full):
        remote_archive_link = f"https://archives.simmate.org/{archive_filename}"
        # Download the archive zip file from the URL to the current working dir
        print("Downloading database file...")
        urllib.request.urlretrieve(remote_archive_link, archive_filename_full)
        print("Done.\n")
    else:
        print(f"Found past download at {archive_filename_full}. Using archive as base.")

    # uncompress the zip file to archive directory
    shutil.unpack_archive(
        archive_filename_full,
        extract_dir=archive_dir,
    )

    # rename and move the sqlite file to be the new database
    db_filename_orig = archive_filename_full.replace(".zip", ".sqlite3")
    db_filename_new = DATABASES["default"]["NAME"]
    shutil.move(db_filename_orig, db_filename_new)
