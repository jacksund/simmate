# -*- coding: utf-8 -*-

"""
This file hosts common functions that are used throughout Simmate
"""

import os
import itertools
from tempfile import TemporaryDirectory, mkdtemp
import shutil
import sys

from dask.distributed import Client, get_client, wait, TimeoutError

from typing import List, Union, Callable


def get_conda_env() -> str:
    """
    Grab the name of the activate conda environment and returns it as a string.
    If there is no env, then an empty string is returned.
    """
    # Check the list of python paths and grab the first path that has "envs" in it.
    # Assume we don't have a conda env until proven otherwise
    env_name = ""
    for path in sys.path:
        if "envs" in path:
            # split the path into individual folder names (os.sep gives / or \\)
            folders = path.split(os.sep)
            # the conda env name will the name immediately after the /envs.
            # example path is '/home/jacksund/anaconda3/envs/simmate_dev/lib/python3.10'
            # where we want the name simmate_dev here.
            env_name = folders[folders.index("envs") + 1]
            # once we have found this, we can exit the loop
            break

    return env_name


def get_doc_from_readme(file: str) -> str:
    """
    Loads the docstring from a README.md file in the same directory.

    This is commonly used in __init__.py files because we like having our
    documentation isolated (so that github renders it).

    To use, simply pass the file property:

    ``` python
    from simmate.utilities import get_doc_from_readme

    __doc__ = get_doc_from_readme(__file__)
    ```

    This is an alternative to using "include" in rst files, which
    [pdoc recommends](https://pdoc.dev/docs/pdoc.html#include-markdown-files).
    We prefer this utility because it allows Spyder to load the docs -- although
    it's slower in production (bc of opening/closing files).
    """

    # We assume the file is in the same directory and named "README.rst"
    file_directory = os.path.dirname(os.path.abspath(file))
    with open(
        os.path.join(file_directory, "README.md"),
        encoding="utf-8",
    ) as doc_file:
        doc = doc_file.read()
    return doc


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

    Parameters
    ----------
    - `directory`:
        Either None, a path to the directory, or a tempdir. The default is None.

    Returns
    -------
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
    return directory


def make_archive(directory: str):
    """
    Compresses the directory to a zip file of the same name. After compressing,
    it then deletes the original directory.

    Parameters
    ----------
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


def empty_directory(directory: str, files_to_keep: List[str] = []):
    """
    Deletes all files and folders within a directory, except for those provided
    to the files_to_keep parameter.

    Parameters
    ----------
    - `directory`:
        base directory that should be emptied
    - `files_to_keep`:
        A list of file and folder names within the base directory that should
        not be deleted. The default is [].
    """
    # grab all of the files and folders inside the listed directory
    for filename in os.listdir(directory):
        if filename not in files_to_keep:
            # check if we have a folder or a file.
            # Folders we delete with shutil and files with the os module
            if os.path.isdir(filename):
                shutil.rmtree(filename)  # ignore_errors=False
            else:
                os.remove(filename)


def get_chemical_subsystems(chemical_system: str):
    """
    Given a chemical system, this returns all chemical systems that are also
    contained within it.

    For example, "Y-C" would return ["Y", "C", "C-Y"]. Note that the returned
    list has elements of a given system in alphabetical order (i.e. it gives
    "C-Y" and not "Y-C")

    Parameters
    ----------
    - `chemical_system`:
        A chemical system of elements. Elements must be separated by dashes (-)

    Returns
    -------
    - `subsystems`:
        A list of chemical systems that make up the input chemical system.
    """

    # TODO: this will may be better located elsewhere. Maybe even as a method for
    # the Composition class.

    # Convert the system to a list of elements
    system_cleaned = chemical_system.split("-")

    # Now generate all unique combinations of these elements. Because we also
    # want combinations of different sizes (nelements = 1, 2, ... N), then we
    # put this in a for-loop.
    subsystems = []
    for i in range(len(system_cleaned)):
        # i is the size of combination we want. We now ask for each unique combo
        # of elements at this given size.
        for combo in itertools.combinations(system_cleaned, i + 1):
            # Combo will be a tuple of elements that we then convert back to a
            # chemical system. We also sort this alphabetically.
            #   ex: ("Y", "C", "F") ---> "C-F-Y"
            subsystem = "-".join(sorted(combo))
            subsystems.append(subsystem)
    return subsystems


def get_dask_client(**kwargs):
    """
    This is a convenience utility that grabs the client for the local Dask cluster
    if it exists -- and if not, creates a new cluster and returns the client for
    it.

    Paramters
    ---------

    - `**kwargs`:
        Any arguments normally accepted by dask.distributed.Client. The exception
        to this is the `preload` kwarg, which is not allowed.
    """

    # First, try accessing a global client.
    try:
        client = get_client()
    # If the line above fails, it's because no global client exists yet. In that
    # case, we make a new cluster and return the client for it.
    except ValueError:
        # This preload script connects each worker to the Simmate database
        client = Client(
            preload="simmate.configuration.dask.connect_to_database",
            **kwargs,
        )

    # OPTIMIZE: I'm not sure if there's a better way to do implement this.
    # If this gives issues, I can alternatively try...
    #   from dask.distributed import client
    #   client._get_global_client()
    # ... based on https://stackoverflow.com/questions/59070260/

    return client


def dask_batch_submit(
    function: Callable,
    args_list: List[dict],
    batch_size: int,
    batch_timeout: float = None,
):
    """
    Given a function and a list of inputs that should be iterated over, this
    submits all inputs to a Dask local cluster in batches.

    This function has very specific use-cases, such as when we are submitting
    >100,000 tasks and each task is unstable / writing to the database. Therefore,
    you should test out Dask normally before trying this utility. Always give
    preference to Dask's `client.map` method over this utility.

    Parameters
    ----------
    - `function`:
        Function that each kwargs entry should be called with.
    - `kwargs_list`:
        A list of parameters that will each be submitted to function via
        function(*args).
    - `batch_size`:
        The number of calls to submit at a time. No new jobs will be
        submitted until the entire preceeding batch completes.
    - `batch_timeout`:
        The timelimit to wait for any given batch before cancelling the remaining
        runs. No error will be raised when jobs are cancelled. The default is
        no timelimit.
    """
    # TODO: I'd like to support a list of kwargs as well
    # TODO: should I add an option to return the results?

    # grab the Dask client
    client = get_dask_client()

    # Iterate through our inputs and submit them to the Dask cluster in batches
    for i in range(0, len(args_list), batch_size):
        chunk = args_list[i : i + batch_size]
        futures = client.map(
            function,
            chunk,
            pure=False,
        )
        try:
            wait(futures, timeout=batch_timeout)
        except TimeoutError:
            client.cancel(futures)
