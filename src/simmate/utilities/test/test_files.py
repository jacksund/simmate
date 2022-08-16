# -*- coding: utf-8 -*-

import shutil

from simmate.conftest import copy_test_files
from simmate.utilities.files import archive_old_runs  # make_archive,
from simmate.utilities.files import empty_directory, get_directory, make_error_archive


def test_get_directory(tmp_path):

    # create and delete a new directory
    new_directory = get_directory()
    assert "simmate-task-" in new_directory.name
    shutil.rmtree(new_directory)

    # get directory by name
    new_directory = get_directory(tmp_path)
    assert tmp_path == new_directory

    # test recursive creation
    subfolder = tmp_path / "subfolder1" / "subfolder2"
    new_directory = get_directory(subfolder)
    assert new_directory == subfolder


def test_make_archive(tmp_path):

    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="to_archive",
    )

    archive_old_runs(tmp_path, time_cutoff=0)
    assert (tmp_path / "simmate-task-1.zip").exists()
    assert (tmp_path / "simmate-task-2.zip").exists()


def test_make_error_archive(tmp_path):

    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="to_archive",
    )

    make_error_archive(tmp_path)
    assert (tmp_path / "simmate_attempt_01.zip").exists()

    make_error_archive(tmp_path)
    assert (tmp_path / "simmate_attempt_02.zip").exists()


def test_empty_directory(tmp_path):

    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="to_archive",
    )

    empty_directory(tmp_path)
    assert not (tmp_path / "simmate-task-1").exists()
    assert not (tmp_path / "simmate-task-2").exists()
