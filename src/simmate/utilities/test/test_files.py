# -*- coding: utf-8 -*-

import shutil

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
    assert "simmate-task-" in new_directory.name
    shutil.rmtree(new_directory)

    # get directory by name
    new_directory = get_directory(tmpdir)
    assert tmpdir == new_directory

    # test recursive creation
    subfolder = tmpdir / "subfolder1" / "subfolder2"
    new_directory = get_directory(subfolder)
    assert new_directory == subfolder


def test_make_archive(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    archive_old_runs(tmpdir, time_cutoff=0)
    assert (tmpdir / "simmate-task-1.zip").exists()
    assert (tmpdir / "simmate-task-2.zip").exists()


def test_make_error_archive(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    make_error_archive(tmpdir)
    assert (tmpdir / "simmate_attempt_01.zip").exists()

    make_error_archive(tmpdir)
    assert (tmpdir / "simmate_attempt_02.zip").exists()


def test_empty_directory(tmpdir):

    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="to_archive",
    )

    empty_directory(tmpdir)
    assert not (tmpdir / "simmate-task-1").exists()
    assert not (tmpdir / "simmate-task-2").exists()
