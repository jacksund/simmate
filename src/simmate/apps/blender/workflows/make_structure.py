# -*- coding: utf-8 -*-

import json
from pathlib import Path

from simmate.apps.blender.config import get_blender_command
from simmate.workflows.common import S3Workflow


class Visualization__Blender__Structure(S3Workflow):
    """
    Creates a 3D model of a crystal structure in Blender.
    """

    use_database = False

    # We don't set a static command because we build it dynamically in
    # get_final_command based on the blender path and script location.

    @classmethod
    def get_final_command(cls, filename="simmate_structure.blend", **kwargs) -> str:
        # load the base blender command for use in function calls below
        blender_command = get_blender_command()

        # The location of the make_structure.py
        executable_directory = Path(__file__).absolute().parent.parent
        path_to_script = executable_directory / "scripts" / "make_structure.py"

        # Now build all of the our serialized structure data and settings together
        # into the blender command that we will call via the command line
        command = (
            f"{blender_command} --background --factory-startup --python {str(path_to_script)} "
            f'-- --filename="simmate_structure.json" --save="{filename}"'
        )
        return command

    @staticmethod
    def setup(directory, structure, **kwargs):
        # This function simply serializes a pymatgen structure object to json
        # and saves it to a file for the blender script to read
        threejs_json = structure.to_json_threejs()
        sites = json.dumps(threejs_json["sites"]).replace('"', "'")
        lattice = json.dumps(threejs_json["lattice"])

        # We package both into a single json dictionary to write to disk
        data = {
            "sites": sites,
            "lattice": lattice,
        }

        with (directory / "simmate_structure.json").open("w") as file:
            json.dump(data, file)

    @staticmethod
    def workup(directory, filename="simmate_structure.blend", **kwargs):
        # we can just return the absolute path to the saved file
        expected_file = directory / filename
        if expected_file.exists():
            return {"file": expected_file}
        else:
            # If the file didn't write, something went wrong, but S3Workflow
            # might have already caught an error. If not, this serves as a check.
            return {}
