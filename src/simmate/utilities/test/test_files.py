# -*- coding: utf-8 -*-

import os
import shutil
from tempfile import TemporaryDirectory

from simmate.conftest import copy_test_files
from simmate.utilities.files import (
    get_directory,
    # make_archive,
    make_error_archive,
    archive_old_runs,
    empty_directory,
)


def test_get_directory(tmpdir):

    # create and delete a new directory
    new_directory = get_directory()
    assert "simmate-task-" in new_directory
    shutil.rmtree(new_directory)

    # get directory by name
    new_directory = get_directory(tmpdir)
    assert tmpdir == new_directory

    # Use a TemporaryDir instance
    tempdir2 = TemporaryDirectory()
    new_directory = get_directory(tempdir2)
    assert new_directory == tempdir2.name
    tempdir2.cleanup()


def test_make_archive(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    archive_old_runs(tmpdir, time_cutoff=0)
    assert os.path.exists(os.path.join(tmpdir, "simmate-task-1.zip"))
    assert os.path.exists(os.path.join(tmpdir, "simmate-task-2.zip"))


def test_make_error_archive(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    make_error_archive(tmpdir)
    assert os.path.exists(os.path.join(tmpdir, "simmate_attempt_01.zip"))

    make_error_archive(tmpdir)
    assert os.path.exists(os.path.join(tmpdir, "simmate_attempt_02.zip"))


def test_empty_directory(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    empty_directory(tmpdir)
    assert not os.path.exists(os.path.join(tmpdir, "simmate-task-1"))
    assert not os.path.exists(os.path.join(tmpdir, "simmate-task-2"))
