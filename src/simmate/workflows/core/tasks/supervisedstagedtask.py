# -*- coding: utf-8 -*-

import os
import time
from shutil import make_archive
from subprocess import Popen

from prefect.core.task import Task
from prefect.utilities.tasks import defaults_from_attrs

from simmate.utilities import get_directory

# This is a combination of prefect ShellTask, custodian Job, and Custodian main.

# from abc import ABC, abstractmethod
# This is really an abstract class that should be overwritten, but I can't have the
# class inherit from both prefect Task and abc's AbstractBaseClass. Therefore,
# I don't strictly enforce writting new setup/execute/postprocess methods.
# I instead trust the user to know what they are doing when inheriting from
# this class (maybe I can fix this in the future.)

# cleanup_on_fail=False, # TODO I should add a Prefect state_handler that can
# reset the working directory between task retries -- in some cases we may
# want to delete the entire directory. As of now, I only ever use retries
# on StagedShellTasks through the SupervisedStagedTask class's ErrorHandlers. Thus
# you should look there for now if you'd like a cleanup_on_fail method.

# OPTIMIZE: I think this class would greatly benefit from asyncio so that we
# know exactly when a shelltask completes, rather than loop and checking every
# set timestep.


class SupervisedStagedShellTask(Task):

    # set a defualt command associated with this specific ShellTask
    # I set this here so that I don't have to copy/paste the init method
    # every time I inherit from this class and want to update the default
    # command to use for the child class.
    command = None

    # Indicates whether you need a structure if you want the run method to work.
    # While it's not needed for a number of cases, it's extremely common for the
    # setup method to need an input structure in matsci. I therefore include
    # this rather than having a nearly identical subclass that could cause
    # some confusion.
    requires_structure = False

    # A list of ErrorHandler objects to use in order of priority (that is, highest
    # priority is first).
    errorhandlers = []

    # maximum number of times we can apply a handler's correction and retry
    # the shelltask
    max_corrections = 5

    # Monitoring settings. These are only ever relevent if there are ErrorHandlers
    # added that have is_monitor=True. These handlers run while the shelltask
    # itself is also running. Read more about ErrorHandlers for more info.

    # Whether to run monitor handlers while the shelltask runs. False means
    # wait until the job has completed.
    monitor = True

    # how often (in seconds) we should check the status of a shelltask if we
    # are also monitoring the job while it runs
    polling_timestep = 10

    # the frequency we should run checks with our monitors. This is based on the
    # polling_timestep loops. For example, if we have a polling_timestep of 10
    # seconds and a monitor_freq of 2, then we would run the monitor checks
    # every other loop -- or every 2*10 = 20 seconds. The default values of
    # polling_timestep=10 and monitor_freq=30 indicate that we run monitoring
    # functions every 5 minutes (10*30=300s=5min).
    monitor_freq = 30

    def __init__(
        self,
        # core parts
        command,
        dir=None,
        errorhandlers=None,
        max_corrections=None,
        # settings for the stagedtask supervision/monitoring
        monitor=None,
        polling_timestep=None,
        monitor_freq=None,
        # this is a common input but not required for all SSSTasks
        structure=None,
        # return, cleanup, and file saving settings
        compress_output=False,
        return_corrections=False,
        save_corrections_tofile=True,
        corrections_filename="simmate_corrections_log.txt",
        # To support other Prefect input options
        **kwargs,
    ):

        # if any of these input parameters were given, overwrite the default
        # Note to python devs: this odd formatting is because we set our defaults
        # to None in __init__ while our actual default values are defined above
        # as class attributes. This may seem funky at first glance, but it
        # makes inheriting from this class extremely pretty :)
        # This code is effectively the same as @defaults_from_attrs(...)
        if command:
            self.command = command
        if structure:
            self.structure = structure
        if errorhandlers:
            self.errorhandlers = errorhandlers
        if monitor:
            self.monitor = monitor
        if max_corrections:
            self.max_corrections = max_corrections
        if polling_timestep:
            self.polling_timestep = polling_timestep
        if monitor_freq:
            self.monitor_freq = monitor_freq

        # These parameters will never have a default which is set to the attribute,
        # so go ahead and set them from what was given in the init
        self.dir = dir
        self.structure = structure
        self.compress_output = compress_output
        self.return_corrections = return_corrections
        self.save_corrections_tofile = save_corrections_tofile
        self.corrections_filename = corrections_filename

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    def setup(self, structure, dir):
        """
        This abstract method is ran before the start of a job. Allows for some
        pre-processing. This includes creating a directory, writing input files
        or any other function ran before calling the executable.
        """
        # Be sure to include dir and structure (or **kwargs) as input arguments for
        # higher-level compatibility with the run method.
        # You should never need to call this method directly!
        pass

    def execute(self, dir):

        # Establish the working directory for this run.
        dir = get_directory(dir)

        # some errorhandlers run while the shelltask is running. These are known as
        # Monitors and are labled via the is_monitor attribute. It's good for us
        # to separate these out from other errorhandlers.
        self.monitors = [
            handler for handler in self.errorhandlers if handler.is_monitor
        ]

        # We start with zero corrections that we slowly add to. This can be
        # thought of as a table with headers of...
        #   ("applied_errorhandler", "error_details", "correction_applied")
        # NOTE: I took out the table headers and may add them back in
        corrections = []

        # we can try running the shelltask up to max_corrections. Because only one
        # correction is applied per attempt, you can view this as the maximum
        # number of attempts made on the calculation.
        while len(corrections) < self.max_corrections:

            # launch the shelltask without waiting for it to complete. Also,
            # make sure to use common shell commands and to set the working
            # directory.
            future = Popen(self.command, cwd=dir, shell=True)

            # Assume the shelltask has no errors until proven otherwise
            has_error = False

            # If monitor=True, then we want to supervise this shelltask as it
            # runs. If montors=[m1,m2,...], then we have monitors in place to actually
            # perform the monitoring. If both of these cases are true, then we
            # want to go through the errorhandlers to check for errors until
            # the shelltask completes.
            if self.monitor and self.monitors:
                # We want to loop until we find an error and keep track of
                # which loops to run the monitor function on because we don't
                # want them to run nonstop. This variable allows us to monitor
                # checks every Nth loop, while we check the shelltask status
                # on all other loops.
                monitor_freq_n = 0
                while not has_error:
                    monitor_freq_n += 1
                    # Sleep the set amount before checking the shelltask status
                    time.sleep(self.polling_timestep)

                    # check if the shelltasks is complete. poll will return 0
                    # when it's done, in which case we break the loop
                    if future.poll() is not None:
                        break

                    # check whether we should run monitors on this poll loop
                    if monitor_freq_n % self.monitor_freq == 0:
                        # iterate through each monitor
                        for errorhandler in self.monitors:
                            # check if there's an error with this errorhandler
                            # and grab the error if so
                            error = errorhandler.check(dir)
                            if error:
                                # determine if it is_terminating
                                if errorhandler.is_terminating:
                                    # kill the process but don't apply the fix
                                    # quite yet. See below for more on this.
                                    future.terminate()
                                # Otherwise apply the fix and let the shelltask end
                                # naturally. An example of this is for codes
                                # where you add a STOP file to get it to
                                # finish rather than just killing the process.
                                # This is the special case errorhandler that I talk
                                # about in my notes, where we really want to
                                # end the shelltask right away.
                                else:
                                    # apply the fix now
                                    correction = errorhandler.correct(error, dir)
                                    # record what's been changed
                                    corrections.append(
                                        (errorhandler.name, error, correction)
                                    )

                                # there's no need to look at the other monitors
                                # so break from the for-loop. We also don't
                                # need to monitor the stagedtask anymore since we just
                                # terminated it or signaled for its graceful
                                # end. So update the while-loop condition.
                                has_error = True
                                break

            # Now just wait for the process to finish
            future.wait()
            # check if the return code is non-zero and thus failed.
            # The 'not has_error' is because terminate() will give a nonzero
            # when a monitor is triggered. We don't want to raise that
            # exception here but instead let the monitor handle that
            # error in the code below.
            if future.returncode != 0 and not has_error:
                raise NonZeroExitError("command failed with non-zero exitcode")

            # Check for errors again, because a non-monitor may be higher
            # priority than the monitor triggered above (if there was one).
            # Since the errorhandlers are in order of priority, only the first
            # will actually be applied and then we can retry the calc.
            for errorhandler in self.errorhandlers:

                # NOTE - The following special case is handled above:
                #   errorhandler.is_monitor and not errorhandler.is_terminating
                # BUG: I can see this being a source of bugs in the future so I
                # need to reconsider subclassing this special case. For now,
                # users should have this case at the lowest priority.

                # check if there's an error with this errorhandler and grab the
                # error if there is one
                error = errorhandler.check(dir)
                if error:
                    # record the error in case it wasn't done so above
                    has_error = True
                    # And apply the proper correction if there is one.
                    # Some errorhandlers will even raise an error here signaling
                    # that the stagedtask is unrecoverable and a lost cause.
                    correction = errorhandler.correct(error, dir)
                    # record what's been changed
                    corrections.append((errorhandler.name, error, correction))
                    # break from the errorhandler for-loop as we only apply the
                    # highest priority fix and nothing else.
                    break

            # now that we've gone through the errorhandlers, let's see if any
            # non-terminating errors were found (terminating ones would raise
            # an error above). If there are no errors, we've finished the
            # calculation and can exit the while loop. Otherwise, just leave
            # everything where it's at and restart the while-loop with a new
            # attempt
            if not has_error:
                # break the while-loop
                break

        # make sure the while loop didn't exit because of the correction limit
        if len(corrections) >= self.max_corrections:
            raise MaxCorrectionsError(
                "the number of maximum corrections has been exceeded"
            )

        # write the log of corrections to file if requested
        if self.save_corrections_tofile:
            with open(self.corrections_filename, "w") as logfile:
                for correction in corrections:
                    logfile.write(f"{correction}\n")

        # if the user wants the corrections returned, return them
        if self.return_corrections:
            return corrections

    def workup(self, dir):
        """
        This method is called at the end of a job, *after* error detection.
        This allows post-processing, such as cleanup, analysis of results,
        etc. This should return the result of the entire job, such as a
        the final structure or final energy calculated.
        """
        # Be sure to include dir (or **kwargs) as input argument for
        # higher-level compatibility with the run method and SupervisedStagedTask
        # You should never need to call this method directly!
        pass

    def postprocess(self, dir):
        # compress the output directory for storage if requested
        if self.compress_output:
            make_archive(
                # full path to where to save the archive
                # !!! By default I choose within the current directory and save
                # !!! it as the same name of the directory. This will be a
                # !!! overwritten if I run another stagedtask right after it.
                # !!! Consider using a unique filename for each save and returning
                # !!! it, or just using a generic simmate_checkpoint name.
                base_name=os.path.join(os.path.abspath(dir), os.path.basename(dir)),
                # format to use switch to gztar after testing
                format="zip",
                # full path to up tp dir that will be archived
                root_dir=os.path.dirname(dir),
                # directory within root_dir to archive
                base_dir=os.path.basename(dir),
            )

    @defaults_from_attrs("structure", "dir")
    def run(
        self,
        structure=None,
        dir=None,
    ):
        """
        Runs the entire job in the current working directory without any error
        handling. If you want robust error handling, then you should instead
        run this through the SupervisedJobTask class. This method should
        very rarely be used!
        """
        # make sure a structure was given if it's required
        if not structure and self.requires_structure:
            raise StructureRequiredError("a structure is required as an input")

        # establish the working directory
        dir = get_directory(dir)

        # run the setup stage of the task
        self.setup(structure, dir)

        # run the shelltask and error supervision stages
        corrections = self.execute(dir)

        # run the workup stage of the task
        result = self.workup(dir)

        # run the postprocess in case any zipping/archiving was requested
        self.postprocess(dir)

        # Based on the input settings, return either the (result, log) or
        # just the result on its own.
        if self.return_corrections:
            return (result, corrections)
        else:
            return result


# Custom errors that indicate exactly what causes the SupervisedStagedTask
# to exit.


class MaxCorrectionsError(Exception):
    pass


class NonZeroExitError(Exception):
    pass


class StructureRequiredError(Exception):
    pass
