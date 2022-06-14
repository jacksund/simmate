# -*- coding: utf-8 -*-

import os
import sys
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
        print(
            "WARNING: There is a new version of Simmate available. \n"
            f"You are currently using v{current_version} while v{latest_version} "
            "is the latest. To update, you should first check what has been "
            "changed at https://github.com/jacksund/simmate/blob/main/CHANGELOG.md. "
            "If you would like to use these changes, you can run the follwing "
            "command in the terminal (with your desired conda environment "
            "active): `conda update --all`"
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
