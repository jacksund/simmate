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


def str_to_datatype(
        parameter: str, 
        value: str,
        type_mappings: dict = {
            "bool_keys": tuple(),
            "float_keys": tuple(),
            "int_keys": tuple(),
            "int_list_keys": tuple(),
            "float_list_keys": tuple(),
            "vector_list_keys": tuple(),
        },
        # OPTIMIZE -- I should set these elsewhere so that these lists are not
        # initialized every time I call this function. Maybe have a dictionary
        # of {Parameter: Value_datatype} in the main enviornment for use.
    ):
    """
    When given a parameter name and it's value as a string, this helper
    function will use the key (parameter) to determine how to convert the
    val string to the proper python datatype (int, float, bool, list...).
    A full mapping of parameters should be provided, but if a parameter is
    given that isn't mapped, the value will be leave left as a string.
    
    This is often ment to read to/from non-standard parameter file formats.
    For example, VASP's INCAR does not follow any standard (yaml, toml, json, 
    etc.) so this function helps read values into python types.
    """

    # If the value is not a string, then assume we are already in the
    # correct format. Note, an incorrect format will throw an error
    # somewhere below, which may be tricky for beginners to traceback.
    if not isinstance(value, str):
        return value

    # if the parameter is in int_keys
    if parameter in int_keys:
        # sometimes "1." was written to indicate an integer so check for
        # this and remove it if needed.
        if value[-1] == ".":
            value = value[:-1]
        # return the value integer
        return int(value)

    # if the parameter is in float_keys, we convert value to a float
    elif parameter in float_keys:
        # return the value float
        return float(value)

    # if the parameter is in bool_keys
    elif parameter in bool_keys:
        # Python is weird where bool("FALSE") will return True... So I need
        # to convert the string to lowercase and read it to know what to
        # return here.
        if "t" in value.lower():
            return True
        elif "f" in value.lower():
            return False

    # if the parameter is in vector_list_keys
    # These vectors are always floats
    elif parameter in vector_list_keys:
        # convert a string of...
        #   "x1 y1 z1 x2 y2 z2 x3 y3 z3"
        # to...
        #   [x1,y1,z1,x2,y2,z2,x3,y3,z3] (list of floats)
        # and then to...
        #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
        value = [float(item) for item in value.split()]
        return [value[i : i + 3] for i in range(0, len(value), 3)]

    # if the parameter is in float_list_keys
    elif parameter in float_list_keys:
        final_list = []
        for item in value.split():
            # Sometimes, the values are given as "3*0.1 2*0.5" where the "*"
            # means to include that value that many times. For example, this
            # input would be the same as "0.1 0.1 0.1 0.5 0.5". We need to
            # account for this when parsing.
            if "*" in item:
                nsubitems, subitem = item.split("*")
                for n in range(int(nsubitems)):
                    final_list.append(float(subitem))
            else:
                final_list.append(float(item))
        return final_list

    # if the parameter is in int_list_keys
    elif parameter in int_list_keys:
        return [int(item) for item in value.split()]

    # If it is not in the common keys listed, just leave it as a string.
    else:
        return value
