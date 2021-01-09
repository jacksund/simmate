# -*- coding: utf-8 -*-

import subprocess

from prefect.core.task import Task
from prefect.utilities.tasks import defaults_from_attrs

from simmate.utilities import get_directory


# this alternative to Prefect.tasks.shell.ShellTask. If I want to add features
# I should use their code as reference. I can also consider merging some of the
# functionality I use here into their code.


class ShellTask(Task):

    # set a defualt command associated with this specific StagedShellTask
    # I set this here so that I don't have to copy/paste the init method
    # every time I inherit from this class and want to update the default
    # command to use for some child class.
    command = None

    def __init__(
        self,
        # optional setup parameters
        command=None,
        dir=None,
        capture_output=True,
        # To support other Prefect input options
        **kwargs,
    ):

        # save setup parameters
        # !!! NOTE TO USER: you really only set these in the init when every
        # time you run the Task these are the same. For example say I have
        # staged VASP job that I want to run multiple time in multiple different
        # places -- in that case I can set the command in it init and leave
        # dir as none. These can be default settings too, which you can
        # overwrite when calling the methods below

        # if a command was given, overwrite the default
        if command:
            self.command = command
        # establish the working directory for this Task
        self.dir = get_directory(dir)
        # whether to record the output
        self.capture_output = capture_output

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    @defaults_from_attrs("dir", "command", "capture_output")
    def run(self, dir, command, capture_output):
        """
        Run a given command and wait for it to complete
        """
        dir = get_directory(dir)

        # run the command
        result = subprocess.run(
            command,
            cwd=dir,  # set the working directory
            shell=True,  # to access commands in the path
            capture_output=capture_output,  # capture any ouput + error logs
        )

        # check if there's a non-zero exitcode
        # note: using check=True above doesn't capture the error message for us
        if result.returncode:
            # if we captured the output, we can add it to Prefect's logger
            # which prints out the error for us
            if capture_output:
                msg = (
                    f"Command failed with exit code {result.returncode}"
                    f" and error message [[ {result.stderr.decode('utf-8')} ]]"
                )
                self.logger.error(msg)
            # now raise the error to make the task fail
            result.check_returncode()

        # return the popen instance
        return result
