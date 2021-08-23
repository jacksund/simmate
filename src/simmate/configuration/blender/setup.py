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


def find_blender_installation():
    """
    Finds the full path to the Blender installation so that we can call blender
    from the command-line. This also adds it's location to the .simmate
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
        raise NotImplementedError(
            "Simmate has not yet added support for Blender on Linux."
            " We can add this right away if you'd like! Just post a request"
            " on our forum."
        )
    
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
            # Note the quotes are important here.
            blender_command = os.path.join(
                expected_folder, blender_version, "blender.exe"
            )

            # now confirm we have this configured properly and can successfully
            # call the blender command.
            blender_test_command = f'"{blender_command}" --version'
            result = subprocess.run(
                blender_test_command,
                shell=True,  # to access commands in the path
                capture_output=True,  # capture any ouput + error logs
            )

            # see if the command works, which means the return code is 0
            assert result.returncode == 0
        # if this path doesn't exist, we need to tell the user to install
        # Blender before than can use any of this functionality.
        else:
            raise Exception(
                "Make sure you have Blender installed before trying to access "
                "any of Simmate's 3D visualization features. If you have already "
                "installed Blender and are seeing this message, then please contact "
                "our team so we can help resolve the issue. If you are unfamiliar "
                "with Blender, take a look at Simmate's tutorial on the topic: "
                " <<TODO: insert link >>"
            )
            
    # Mac -- I don't own a Mac so I haven't implemented this yet.
    elif operating_system == "Darwin":
        raise NotImplementedError(
            "Simmate has not yet added support for Blender on Macs."
            " We can add this right away if you'd like! Just post a request"
            " on our forum."
        )
    
    
    # We should now have our blender_command set from above. So that we don't need
    # to search for the Blender installation every time we call a visualization
    # function, we want to save the path to a configuration file in /.simmate
    # TODO---------------------------------------------------------------------------------------------------
    
    return blender_command


def get_blender_command():
    
    # loads the blender command
    # First we look in the .simmate configuration directory and check if it
    # has been set there. If not, we then try to find blender using the
    # find_blender_installation function defined above.
    
    pass
