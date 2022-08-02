# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory, mkdtemp
import shutil
import time
from typing import List, Union


def get_directory(directory: Union[str, TemporaryDirectory] = None) -> str:
    """
    Initializes a directory.

    There are many cases where the user can choose their working directory
    for a calculation, and they may want to provide their directory in various
    formats. This includes... None, a string, or a TemporaryDirectory instance.
    Based on the input, this function does the following:
      - `None`:
          returns the full path to a new folder inside python's
          current working directory named "simmate-task-<randomID>"
      - `TemporaryDirectory`:
          returns the full path to the given temp directory
      - `str`:
          makes the directory if it doesnt exist and then returns the path

    #### Parameters

    - `directory`:
        Either None, a path to the directory, or a tempdir. The default is None.

    #### Returns

    - `directory`:
        The path to the initialized directory as a string
    """

    # if no directory was provided, we create a new folder within the current
    # working directory. All of these folders are named randomly.
    # Note: we can't name these nicely (like simmate-task-001) because that will
    # introduce race conditions when making these folders in production.
    if not directory:
        # create a directory in the current working directory. Note, even though
        # we are creating a "TemporaryDirectory" here, this directory is never
        # actually deleted.
        directory = mkdtemp(prefix="simmate-task-", dir=os.getcwd())

    # if the user provided a tempdir, we want it's name
    elif isinstance(directory, TemporaryDirectory):
        directory = directory.name

    # otherwise make sure the directory the user provided exists and if it does
    # not, then make it!
    else:
        # We use mkdirs instead of mkdir because we want to make these directory
        # recursively. That is, we can do "path/to/newfolder1/newfolder2" where
        # multiple folders can be made with one call.
        # Also if the folder already exists, we don't want to raise an error.
        os.makedirs(directory, exist_ok=True)

    # and return the full path to the directory
    return os.path.abspath(directory)


def copy_directory(
    directory_old: str,
    directory_new: str = None,
    ignore_simmate_files: bool = False,
) -> str:
    """
    Given an old directory, copies all of it's contents over to a new one.
    Optionally, you can avoid copying any simmate_* files and archives within
    that original directory to save on disk space.

    #### Parameters

    - `directory_old`:
        Name of the directory to be copied over. Must exist.

    - `directory_new`:
        Name of the new directory (optional). This will be passed to the
        `get_directory` utility.

    - `ignore_simmate_files`:
        Whether to ignore simmate_* files when copying over. Defaults to False.

    #### Returns

    - `directory`:
        The path to the new directory as a string

    """

    # Start by creating a new directory or grabbing the one given.
    directory_new_cleaned = get_directory(directory_new)

    # First check if the previous directory exists. There are several
    # possibilities that we need to check for:
    #   1. directory exists on the same file system and can be found
    #   2. directory exists on the same file system but is now an archive
    #   3. directory/archive is on another file system (requires ssh to access)
    #   4. directory was deleted and unavailable
    # When copying over the directory, we ignore any `simmate_` files
    # that correspond to metadata/results/corrections/etc.
    if os.path.exists(directory_old):
        # copy the old directory to the new one
        shutil.copytree(
            src=directory_old,
            dst=directory_new_cleaned,
            ignore=shutil.ignore_patterns("simmate_*")
            if ignore_simmate_files
            else None,
            dirs_exist_ok=True,
        )
    elif os.path.exists(f"{directory_old}.zip"):
        # unpack the old archive
        shutil.unpack_archive(
            filename=f"{directory_old}.zip",
            extract_dir=os.path.dirname(directory_old),
        )
        # copy the old directory to the new one
        shutil.copytree(
            src=directory_old,
            dst=directory_new_cleaned,
            ignore=shutil.ignore_patterns("simmate_*")
            if ignore_simmate_files
            else None,
            dirs_exist_ok=True,
        )
        # Then remove the unpacked archive now that we copied it.
        # This leaves the original archive behind and unaltered too.
        shutil.rmtree(directory_old)
    else:
        raise Exception(
            "Unable to locate the previous directory to copy. Make sure the "
            "past directory is located on the same file system. Directory that "
            f"couldn't be found was... {directory_old}"
        )
    # TODO: for possibility 3, I could implement automatic copying with
    # the "fabric" python package (uses ssh). I'd also need to store
    # filesystem names (e.g. "WarWulf") to know where to connect.

    return directory_new_cleaned


def make_archive(directory: str):
    """
    Compresses the directory to a zip file of the same name. After compressing,
    it then deletes the original directory.

    #### Parameters

    - `directory`:
        Path to the folder that should be archived
    """
    # This wraps shutil.make_archive to change the default parameters. Normally,
    # it writes the archive in the working directory, but we update it to use the
    # the same directory as the folder being archived. The format is also set
    # to zip.
    shutil.make_archive(
        # By default I choose within the current directory and save
        # it as the same name of the directory (+ zip ending)
        base_name=os.path.abspath(directory),
        # format to use switch to gztar after testing
        format="zip",
        # full path to up tp directory that will be archived
        root_dir=os.path.dirname(directory),
        # directory within root_directory to archive
        base_dir=os.path.basename(directory),
    )
    # now remove the directory we just archived
    shutil.rmtree(directory)


def make_error_archive(directory: str):
    """
    Compresses the directory to a zip file and stores the new archive within the
    original. This utility is meant for creating archives within the directory
    of a failed calculation, so the new archive will be named something like
    `simmate_attempt_01.zip`, where the number is automatically determined. When
    archiving the folder, all "simmate_*" files within the directory are ignore
    (this is includes earlier simmate_attempt_*.zip archives).

    #### Parameters

    - `directory`:
        Path to the folder that should be archived
    """

    full_path = os.path.abspath(directory)

    # check the directory and see how many other "simmate_attempt_*.zip" files
    # already exist. Our archive number will be based off of this.
    count = (
        len([f for f in os.listdir(full_path) if f.startswith("simmate_attempt_")]) + 1
    )
    count_str = str(count).zfill(2)
    base_name = os.path.join(full_path, f"simmate_attempt_{count_str}")

    # Before we make the archive, we want to avoid also storing other simmate
    # archives and files within this new archive. We therefore copy all files
    # that do NOT start with "simmate_" over into a folder and then archive it.
    shutil.copytree(
        src=full_path,
        dst=base_name,
        ignore=shutil.ignore_patterns("simmate_*"),
    )

    # now convert the copied files to a new archive
    make_archive(base_name)


def archive_old_runs(
    directory: str = ".",
    time_cutoff: float = 3 * 7 * 24 * 60 * 60,  # equal to 3 weeks
):
    """
    Goes through a given directory and finds all "simmate-task-" folders that
    are older than a given time cutoff. Each of these folders is then compressed
    to a zip file and then the original folder is removed.

    #### Parameters

    - `directory`:
        base directory that will contain folders to archive. Defaults to the
        working directory.
    - `time_cutoff`:
        The time (in seconds) required to determine whether a folder is old or not.
        If the folder is considered old, then it will be archived and then deleted.
        The default is 3 weeks.

    """
    # load the full path to the desired directory
    directory = get_directory(directory)

    # grab all files/folders in this directory and then limit this list to those
    # that are...
    #   1. folders
    #   2. start with "simmate-task-"
    #   3. haven't been modified for at least time_cutoff
    foldernames = []
    for foldername in os.listdir(directory):
        foldername_full = os.path.join(directory, foldername)
        if (
            os.path.isdir(foldername_full)
            and "simmate-task-" in foldername
            and time.time() - os.path.getmtime(foldername_full) > time_cutoff
        ):
            foldernames.append(foldername_full)

    # now go through this list and archive the folders that met the criteria
    [make_archive(f) for f in foldernames]


def empty_directory(directory: str, files_to_keep: List[str] = []):
    """
    Deletes all files and folders within a directory, except for those provided
    to the files_to_keep parameter.

    #### Parameters

    - `directory`:
        base directory that should be emptied
    - `files_to_keep`:
        A list of file and folder names within the base directory that should
        not be deleted. The default is [].
    """
    # grab all of the files and folders inside the listed directory
    for filename in os.listdir(directory):
        full_path = os.path.join(directory, filename)
        if filename not in files_to_keep:
            # check if we have a folder or a file.
            # Folders we delete with shutil and files with the os module
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)  # ignore_errors=False
            else:
                os.remove(full_path)
