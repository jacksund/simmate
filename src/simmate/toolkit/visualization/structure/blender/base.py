# -*- coding: utf-8 -*-

import json
import subprocess
from pathlib import Path

from simmate.toolkit.visualization.structure.blender.configuration import (
    get_blender_command,
)


def make_blender_structure(structure, filename="simmate_structure.blend"):
    # load the base blender command for use in function calls below
    BLENDER_COMMAND = get_blender_command()
    # OPTIMIZE: ideally I would load this outside the function so that it is only
    # loaded once. Here, I read a yaml file repeatedly. There should be a better
    # way to silently catch errors when blender isn't installed.

    # This function simply serializes a pymatgen structure object to json
    # and then calls a blender script (make_structure.py) that uses this data
    # BUG: Make sure strings are dumped using single quotes so that this
    # doesn't conflict with the command line.
    threejs_json = structure.to_json_threejs()
    sites = json.dumps(threejs_json["sites"]).replace('"', "'")
    lattice = json.dumps(threejs_json["lattice"])

    # The location of the make_structure.py
    executable_directory = Path(__file__).absolute().parent
    path_to_script = executable_directory / "scripts" / "make_structure.py"

    # Now build all of the our serialized structure data and settings together
    # into the blender command that we will call via the command line
    command = (
        f"{BLENDER_COMMAND} --background --factory-startup --python {str(path_to_script)} "
        f'-- --sites="{sites}" --lattice="{lattice}" --save="{filename}"'
    )

    # Now run the command
    result = subprocess.run(
        command,
        shell=True,  # to access commands in the path
        capture_output=True,  # capture any ouput + error logs
    )

    return result
