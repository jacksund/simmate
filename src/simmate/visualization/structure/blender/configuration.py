# -*- coding: utf-8 -*-

# Calling Blender is currently a messy business because there's no easy
# way to install it as a python module. Instead we need to install Blender
# separately and have it execute scripts from the command-line. To do this,
# we need to check and see if Blender is installed, and if not, warn the user.
# This is different for each operating system, and each is outlined here:
#   https://docs.blender.org/manual/en/latest/advanced/command_line/launch/index.html

import os
import platform
import subprocess
from pathlib import Path

import yaml

# NOTE: You should only need to use the get_blender_command() function below.
# All other functions are called within it.
#
# The exception to this is if you installed a new version of Blender when you
# already had a older version configured. In this case, just run the
# find_blender_installation once and you're good to go!


def get_blender_command():

    # First we look in the simmate configuration directory and check if it
    # has been set there.
    #   [home_directory] ~/simmate/blender.yaml
    blender_filename = os.path.join(Path.home(), "simmate", "blender.yaml")
    if os.path.exists(blender_filename):
        with open(blender_filename) as file:
            blender_command = yaml.full_load(file)["COMMAND"]

        # BUG: for windows, we need to add quotes around the command because
        # it's actually a path. I couldn't figure out how to store these quotes
        # directly in the yaml file...
        if platform.system() == "Windows":
            blender_command = f'"{blender_command}"'

    # If not, we then try to find blender using the find_blender_installation
    # function defined below.
    else:
        blender_command = find_blender_installation()

    test_blender_command(blender_command)

    # we should now have the blender command and can return it for use elsewhere
    return blender_command


def find_blender_installation():
    """
    Finds the full path to the Blender installation so that we can call blender
    from the command-line. This also adds it's location to the simmate
    configuration folder so that we don't need to search for it every time.
    """

    # The operating system (Windows, OSX, or Linux) will give us the best guess
    # as to where to access the blender command. The results are as you'd expect
    # except for Macs, which return "Darwin".
    #   Linux: Linux
    #   Mac: Darwin
    #   Windows: Windows
    operating_system = platform.system()

    # Linux includes all distros where we primarily test with Ubuntu.
    if operating_system == "Linux":

        # On Linux, we actually have the easiest setup because the blender
        # command should be directly accessible -- regardless of where blender
        # was installed.
        blender_command = "blender"

    # Windows -- we assume Windows 10 for now.
    elif operating_system == "Windows":

        # On Windows, Blender is typically installed in the following directory:
        #   C:\Program Files\Blender Foundation\Blender 2.93
        expected_folder = "C:\\Program Files\\Blender Foundation\\"
        # in the future, I could have a list of directories to check here and
        # then iterate through them below.

        # We check the folder, and if it exists we grab the highest Blender version listed.
        if os.path.exists(expected_folder):

            # grab all the folders and find the highest blender version, which
            # be the last one when sorted alphabetically
            blender_version = sorted(os.listdir(expected_folder))[-1]

            # To call blender in python, we write the full path to the blender
            # executable. For example, the command looks like this:
            #   "C:\\Program Files\\Blender Foundation\\Blender 2.93\\blender.exe" --help
            full_path_to_blender = os.path.join(
                expected_folder, blender_version, "blender.exe"
            )
            # Because there are spaces in the file path, it is important we
            # wrap this command in quotes. Note we also replace the backslashes
            # in the file path with forward slashes.
            blender_command = f'"{full_path_to_blender}"'.replace("\\", "/")

        # if this path doesn't exist, we need to tell the user to install
        # Blender before than can use any of this functionality.
        else:
            raise BlenderNotInstalledError

    # Mac -- I don't own a Mac so I haven't implemented this yet.
    elif operating_system == "Darwin":
        raise NotImplementedError(
            "Simmate has not yet added support for Blender on Macs."
            " We can add this right away if you'd like! Just post a request"
            " on our forum."
        )

    # now confirm we can call the blender command
    test_blender_command(blender_command)

    # We should now have our blender_command set from above. So that we don't need
    # to search for the Blender installation every time we call a visualization
    # function, we want to save the path to a configuration file in /simmate

    # We store the command inside the config directory which is located at...
    #   [home_directory] ~/simmate/blender.yaml
    blender_filename = os.path.join(Path.home(), "simmate", "blender.yaml")
    with open(blender_filename, "w") as file:
        file.write(f"COMMAND: {blender_command}")

    return blender_command


def test_blender_command(blender_command):
    # To confirm we have blender configured properly, we often need to test it
    # out. We do this by calling the "blender --help" command
    command_to_test = f"{blender_command} --version"
    result = subprocess.run(
        command_to_test,
        shell=True,  # to access commands in the path
        capture_output=True,  # capture any ouput + error logs
    )

    # see if the command works, which means the return code is 0
    if result.returncode != 0:
        raise BlenderNotInstalledError


class BlenderNotInstalledError(Exception):
    def __init__(self):
        default_message = (
            "Make sure you have Blender installed before trying to access "
            "any of Simmate's 3D visualization features. If you have already "
            "installed Blender and are seeing this message, then please contact "
            "our team so we can help resolve the issue. You can download Blender "
            "from their website: https://www.blender.org/download/"
        )
        super().__init__(default_message)
