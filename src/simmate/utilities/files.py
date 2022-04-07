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
    # the same directory that the folder being archived. The format is also set
    # to zip
    shutil.make_archive(
        # By default I choose within the current directory and save
        # it as the same name of the directory (+ zip ending)
        base_name=os.path.join(os.path.abspath(directory)),
        # format to use switch to gztar after testing
        format="zip",
        # full path to up tp directory that will be archived
        root_dir=os.path.dirname(directory),
        # directory within root_directory to archive
        base_dir=os.path.basename(directory),
    )
    # now remove the directory we just archived
    shutil.rmtree(directory)


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
