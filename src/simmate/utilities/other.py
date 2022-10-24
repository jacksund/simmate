# -*- coding: utf-8 -*-

import logging
import os
import sys
from pathlib import Path

import requests

import simmate


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


def get_latest_version() -> str:
    """
    Looks at the jacks/simmate repo and grabs the latest release version.
    """
    # Access the data via a web request
    response = requests.get(
        "https://api.github.com/repos/jacksund/simmate/releases/latest"
    )

    # load the version from the json response
    # [1:] simply removes the first letter "v" from something like "v1.2.3"
    latest_version = response.json()["tag_name"][1:]
    return latest_version


def check_if_using_latest_version(current_version=simmate.__version__):
    """
    Checks if there's a newer version by looking at the latest release on Github
    and comparing it to the currently installed version
    """
    latest_version = get_latest_version()

    if current_version != latest_version:
        logging.warning(
            "There is a new version of Simmate available. "
            f"You are currently using v{current_version} while v{latest_version} "
            "is the latest."
        )


def get_chemical_subsystems(chemical_system: str):
    """
    Given a chemical system, this returns all chemical systems that are also
    contained within it.

    For example, "Y-C" would return ["Y", "C", "C-Y"]. Note that the returned
    list has elements of a given system in alphabetical order (i.e. it gives
    "C-Y" and not "Y-C")

    #### Parameters

    - `chemical_system`:
        A chemical system of elements. Elements must be separated by dashes (-)

    #### Returns

    - `subsystems`:
        A list of chemical systems that make up the input chemical system.
    """

    # TODO: this code may be better located elsewhere. Maybe even as a method for
    # the Composition class or alternatively as a ChemicalSystem class.

    # I convert the system to a composition where the number of atoms dont
    # apply here. (e.g. "Ca-N" --> "Ca1 N1")
    from simmate.toolkit import Composition

    composition = Composition(chemical_system.replace("-", ""))

    return composition.chemical_subsystems


def chunk_list(full_list: list, chunk_size: int) -> list:
    """
    Yield successive n-sized chunks from a list.
    """
    for i in range(0, len(full_list), chunk_size):
        yield full_list[i : i + chunk_size]
