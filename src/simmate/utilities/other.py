# -*- coding: utf-8 -*-

import importlib
import logging
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
    Yields successive n-sized chunks from a list.
    """
    for i in range(0, len(full_list), chunk_size):
        yield full_list[i : i + chunk_size]


def str_to_datatype(
    parameter: str,
    value: str,
    type_mappings: dict = {},
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

    Example type_mapping using random VASP settings:
    ``` python
    type_mapping = {
        "LDAU": bool,
        "EDIFF": float,
        "NSW": int,
        "LDAUL": list[int],
        "LDAUU": list[float],
        "DIPOL": list[list[float]],
    }
    ```
    """

    # If the value is not a string, then assume we are already in the
    # correct format. Note, an incorrect format will throw an error
    # somewhere below, which may be tricky for beginners to traceback.
    if not isinstance(value, str):
        return value

    # next, try grabbing the type from mapping dictionary. If the parameter is
    # not mapped, then we assume it is a str.
    target_type = type_mappings.get(parameter, str)

    # Now that we know the target type to convert to, we can go through
    # decide how to handle converting the value

    if target_type == str:
        # assert type(value) == str
        return value

    elif target_type == int:
        # sometimes "1." was written to indicate an integer so check for
        # this and remove it if needed.
        if value[-1] == ".":
            value = value[:-1]
        # return the value integer
        return int(value)

    elif target_type == float:
        # return the value float
        return float(value)

    elif target_type == bool:
        # Python is weird where bool("FALSE") will return True... So I need
        # to convert the string to lowercase and read it to know what to
        # return here.
        if "t" in value.lower():
            return True
        elif "f" in value.lower():
            return False

    elif target_type == list[float]:
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

    elif target_type == list[int]:
        return [int(item) for item in value.split()]

    # These vectors are always 3x floats
    elif target_type == list[list[float]]:
        # convert a string of...
        #   "x1 y1 z1 x2 y2 z2 x3 y3 z3"
        # to...
        #   [x1,y1,z1,x2,y2,z2,x3,y3,z3] (list of floats)
        # and then to...
        #   [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
        value = [float(item) for item in value.split()]
        return [value[i : i + 3] for i in range(0, len(value), 3)]

    # If it is not in the common keys listed, just leave it as a string.
    else:
        logging.warning(
            "Unknown parameter mapping of {parameter}: {target_type}. "
            "Leaving as str."
        )
        return value


def get_class(class_path: str):
    """
    Given the import path for a python class (e.g. path.to.MyClass), this
    utility will load the class given (MyClass).
    """
    config_modulename = ".".join(class_path.split(".")[:-1])
    config_name = class_path.split(".")[-1]
    config_module = importlib.import_module(config_modulename)
    config = getattr(config_module, config_name)
    return config


def get_app_submodule(
    app_name: str,
    submodule_name: str,
) -> str:
    """
    Checks if an app has a submodule present and returns the import path for it.
    This is useful for checking if there are workflows or urls defined, which
    are optional accross all apps. None is return if no app exists
    """
    config = get_class(app_name)
    app_path = config.name
    submodule_path = f"{app_path}.{submodule_name}"

    # check if there is a workflows module in the app, and if so,
    # try loading the workflows.
    #   stackoverflow.com/questions/14050281
    has_submodule = importlib.util.find_spec(submodule_path) is not None

    return submodule_path if has_submodule else None
