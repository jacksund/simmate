# -*- coding: utf-8 -*-

from subprocess import Popen

from prefect.core.task import Task
from prefect.utilities.tasks import defaults_from_attrs

from simmate.utilities import get_directory


# cleanup_on_fail=False, # TODO I should add a Prefect state_handler that can
# reset the working directory between task retries -- in some cases we may
# want to delete the entire directory. As of now, I only ever use retries
# on StagedTasks through the SupervisedStagedTask class's ErrorHandlers. Thus
# you should look there for now if you'd like a cleanup_on_fail method.

# from abc import ABC, abstractmethod
# This really an abstract class that should be overwritten, but I can't have the
# class inherit from both prefect Task and abc's AbstractBaseClass. Therefore,
# I don't strictly enforce writting new setup/execute/postprocess methods.
# I instead trust the user to know what they are doing when inheriting from
# this class (maybe I can fix this in the future.)

# This is a combination of prefect ShellTask and custodian Job


class StagedShellTask(Task):
    """
    Abstract base class defining a Task that should be used with SupervisedJobTask
    if you want error handling. Only use this if you have a bunch of Handlers
    to perform error correction on a running Task. 99% of the time you are doing
    this when you call some executable that creates a bunch of output files.
    For example, we may want to read VASP output files as the job runs and
    also after it finishes to look for errors and then retry the calculation based
    off of those errors with updated settings.
    """

    # set a defualt command associated with this specific StagedShellTask
    # I set this here so that I don't have to copy/paste the init method
    # every time I inherit from this class and want to update the default
    # command to use for the child class.
    command = None

    def __init__(
        self,
        # optional setup parameters
        command=None,
        dir=None,
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

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    @defaults_from_attrs("dir")
    def setup(self, dir):
        """
        This method is run before the start of a job. Allows for some
        pre-processing. This includes creating a directory, writing input files
        or any other function ran before calling the executable.
        """
        # NOTE TO USER: you will need this line if your function is directory
        # specific and even if not, be sure to include dir (or **kwargs) as
        # input argument for higher-levl compatibility with SupervisedStagedTask
        # dir = get_directory(dir)
        pass

    @defaults_from_attrs("dir", "command")
    def execute(self, dir, command, wait_until_complete=False):
        """
        This method performs the actual work for the job. If parallel error
        checking (monitoring) is desired, this must return a Popen process.
        Otherwise, this code should wait until the calculation finishes.
        The return of conncurrent.futures is not yet supported.
        This is name execute instead of run to help stay consistent with
        Prefect Task formats used elsewhere.
        """
        # 99% of the time this class is used, the execute method should simply
        # start a subprocess and return the Popen "future". You can overwrite
        # this method if you'd like as its just a default function
        dir = get_directory(dir)

        # run the command in the proper directory
        future = Popen(command, cwd=dir, shell=True)

        # see if the user wants to wait until the command is completed
        if wait_until_complete:
            future.wait()

        # return the popen instance
        return future

    @defaults_from_attrs("dir")
    def postprocess(self, dir):
        """
        This method is called at the end of a job, *after* error detection.
        This allows post-processing, such as cleanup, analysis of results,
        etc. This should return the result of the entire job, such as a
        the final structure or final energy calculated.
        """
        # NOTE TO USER: you will need this line if your function is directory
        # specific and even if not, be sure to include dir (or **kwargs) as
        # input argument for higher-levl compatibility with SupervisedStagedTask
        # dir = get_directory(dir)
        pass

    @defaults_from_attrs("dir", "command")
    def run(self, dir, command):
        """
        Runs the entire job in the current working directory without any error
        handling. If you want robust error handling, then you should instead
        run this through the SupervisedJobTask class. This method should
        very rarely be used!
        """
        dir = get_directory(dir)
        self.setup(dir=dir)
        self.execute(command=command, dir=dir, wait_until_complete=True)
        result = self.postprocess(dir=dir)
        return result
