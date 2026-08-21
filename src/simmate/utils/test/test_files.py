# -*- coding: utf-8 -*-

import shutil

from simmate.conftest import copy_test_files
from simmate.utils.files import empty_directory, get_directory


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


def test_empty_directory(tmp_path):
    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="to_archive",
    )

    empty_directory(tmp_path)
    assert not (tmp_path / "simmate-task-1").exists()
    assert not (tmp_path / "simmate-task-2").exists()


def test_make_archive(tmp_path):
    from simmate.utils.files import make_archive

    copy_test_files(
        tmp_path,
        test_directory=__file__,
        test_folder="to_archive",
    )
    folder = tmp_path / "simmate-task-1"
    make_archive(folder)
    assert (tmp_path / "simmate-task-1.zip").exists()
    assert not folder.exists()
