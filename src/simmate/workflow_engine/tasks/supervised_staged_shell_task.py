# -*- coding: utf-8 -*-

import os
import platform
import time
import signal
import subprocess
import yaml

import pandas

import prefect
from prefect.core.task import Task
from prefect.utilities.tasks import defaults_from_attrs

from simmate.utilities import get_directory, make_archive

from typing import List, Any
from simmate.toolkit import Structure
from simmate.workflow_engine.error_handler import ErrorHandler

# cleanup_on_fail=False, # TODO I should add a Prefect state_handler that can
# reset the working directory between task retries -- in some cases we may
# want to delete the entire directory.

# OPTIMIZE: I think this class would greatly benefit from asyncio so that we
# know exactly when a shelltask completes, rather than looping and checking every
# set timestep.
# https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.create_subprocess_exec


class S3Task(Task):
    """
    The Supervised-Staged-Shell Task (aka "S3Task")
    -----------------------------------------------

    This class contains the core functionality to **supervise** a **staged** task
    involving some **shell** command.

    Let's breakdown what this means...

    A *shell* command is a single call to some external program. For example,
    VASP requires that we call the "vasp_std > vasp.out" command in order to run a
    calculation. We consider calling external programs a *staged* task made
    up of three steps:

    - setup = writing any input files required for the program
    - execution = actually calling the command and running our program
    - workup = loading data from output files back into python

    And for *supervising* the task, this means we monitor the program while the
    execution stage is running. So once a program is started, Simmate can check
    output files for common errors/issues. If an error is found, we stop the
    program, fix the issue, and then restart it. Any fixes that were made are
    written to "simmate_corrections.csv".


    <!--
    TODO: Make a simple diagram to visualize the overall process and add it here.
    It will be similar to Custodian's, but we don't have a list of jobs here.
    https://materialsproject.github.io/custodian/index.html#usage
    The steps are...

    - Write Input Files based on custom+defualt settings
    - Run the calculation by calling the program
    - Load ouput files
    - check for errors
    - [correct them, rerun]
    - postprocess/analysis
    -->

    This entire process (the different stages and monitoring) is carried out
    using the ``run()`` method. You rarely use this class directly. Instead,
    you typically use a subclass of it. As a user, you really just need to do
    something like this:

    ``` python
       from simmate.calculator.example.tasks import ExampleTask

       my_task = ExampleTask()
       my_result = my_task.run()
    ```

    And that's it!

    For experts, this class can be viewed as a combination of prefect's ShellTask,
    a custodian Job, and Custodian monitoring. When subclassing this, we can absorb
    functionality of pymatgen.io.vasp.sets too. By merging all of these together
    into one class, we make things much easier for users and creating new Tasks.


    Inheriting from this class
    --------------------------

    This class is commonly used to make tasks for our calculator modules, so you
    will likely want to subclass this. Here is a basic example of inheriting
    and then running a task:

    ``` python

    from simmate.workflow_engine import S3Task
    from example.error_handlers import PossibleError1, PossibleError2


    class ExampleTask(SSSTask):

        command = "echo example"  # just prints out "example"
        max_corrections = 7
        error_handlers = [PossibleError1, PossibleError2]
        polling_timestep = 0.1
        monitor_freq = 10
        some_new_setting = 123

        def setup(self, structure, directory):  # <-- MUST have these two args
            print("I'm setting things up!")
            print(f"My new setting is {some_new_setting}")

        def workup(self, directory):  # <-- MUST have this arg
            print("I'm working things up!")


    task = ExampleTask()
    result = task.run()
    ```

    There are a couple things to note here:

    - It's optional to set/overwrite attributes. You can also add new ones too.
    - It's optional to write a new __init__, setup, or workup methods
    - make sure you include the structure/directory inputs, even if you don't use them.
    - Don't add new kwargs to methods. Instead handle these options through attributes.

    For a full (and advanced) example, of a subclass take a look at
    `simmate.calculators.vasp.tasks.base.VaspTask`.

    """

    # I set this here so that I don't have to copy/paste the init method
    # every time I inherit from this class and want to update the default
    # command to use for the child class.
    command: str = None
    """
    The defualt shell command to use.
    """

    # While it's not needed for a number of cases, it's extremely common for the
    # setup method to need an input structure in matsci. I therefore include
    # this rather than having a nearly identical subclass that could cause
    # some confusion.
    requires_structure: bool = False
    """
    Indicates whether a structure is needed if for the run() method.
    """

    error_handlers: List[ErrorHandler] = []
    """
    A list of ErrorHandler objects to use in order of priority (that is, highest
    priority is first). If one handler is triggered, the correction will be 
    applied and none of the following handlers will be checked.
    """

    def __init__(
        self,
        max_corrections: int = 5,
        monitor: bool = True,
        polling_timestep: float = 1,
        monitor_freq: int = 300,
        save_corrections_to_file: bool = True,
        corrections_filename: str = "simmate_corrections.csv",
        compress_output: bool = False,
        **kwargs: Any,
    ):
        """
        Creates a task instance of this class. The parameters passed will be the
        same every time you call the task.run() method.

        Note, many of the parameters here are for the Monitoring settings. These
        are only ever relevent if there are ErrorHandlers added that have
        is_monitor=True. These handlers run while the shelltask itself is also
        running. Read more about ErrorHandlers for more info.

        Parameters
        ----------
        - `max_corrections`:
            The maximum number of times we can apply a correction and retry the shell
            command. The maximum number of times that corrections will be made (and
            shell command reran) before giving up on the calculation. Note, once this
            limit is exceeded, the error is stored without correcting or restarting
            the run.
        - `monitor`:
            Whether to run monitor handlers while the command runs. False means
            wait until the job has completed.
        - `polling_timestep`:
            If we are monitoring the job for errors while it runs, this is how often
            (in seconds) we should check the status of our job. Note this check is
            just whether the job is done or not. This is NOT how often we check for
            errors. See monitor_freq for that.
        - `monitor_freq`:
            The frequency we should run check for errors with our monitors. This is
            based on the polling_timestep loops. For example, if we have a
            polling_timestep of 10 seconds and a monitor_freq of 2, then we would run
            the monitor checks every other loop -- or every 2x10 = 20 seconds. The
            default values of polling_timestep=10 and monitor_freq=30 indicate that
            we run monitoring functions every 5 minutes (10x30=300s=5min).
        - `save_corrections_to_file`:
            Whether to write a log file of the corrections made. The default is True.
        - `corrections_filename`:
            If save_corrections_to_file is True, this is the filename of where
            to write the corrections. The default is "simmate_corrections.csv".
        - `compress_output`:
            Whether to compress the directory to a zip file at the end of the
            task run. After compression, it will also delete the directory.
            The default is False.
        - `**kwargs`:
            All extra arguments supported by
            [prefect.core.task.Task](https://docs.prefect.io/api/latest/core/task.html).
        """

        # Save the provided settings
        self.monitor = monitor
        self.max_corrections = max_corrections
        self.polling_timestep = polling_timestep
        self.monitor_freq = monitor_freq
        self.compress_output = compress_output
        self.save_corrections_to_file = save_corrections_to_file
        self.corrections_filename = corrections_filename

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    def setup(self, structure: Structure, directory: str, **kwargs):
        """
        This abstract method is ran before the command is actually executed. This
        allows for some pre-processing, such as writing input files or any other
        analysis.

        You should never call this method directly unless you are debugging. This
        is becuase setup() is normally called within the run() method.

        Some tasks don't require a setup() method, so by default, this method
        doesn't nothing but "pass".

        Parameters
        ----------
        - `structure`:
            The structure to use for the task, if one is required.
        - `directory`:
            The directory to run everything in. Must exist already.
        - `**kwargs`:
            Extra kwargs that may be passed to some function within. Because
            Simmate prefers fixed settings for their workflows, this is typically
            not used, but instead, keywords should be explicitly defined when
            writing a setup method.
        """
        # Be sure to include directory and structure (or **kwargs) as input
        # arguments for higher-level compatibility with the run method.
        pass

    def execute(self, directory: str, command: str):
        """
        This calls the command within the target directory and handles all error
        handling as well as monitoring of the job.

        You should never call this method directly unless you are debugging. This
        is becuase `execute` is normally called within the `run` method.

        Some tasks don't require a setup() method, so by default, this method
        does nothing but "pass".

        Parameters
        ----------
        - `directory`:
            The directory to run everything in.
        - `command`:
            The command that will be called during execution.

        Returns
        -------
        - `corrections`
            A list of tuples where each entry is a error identified and the
            correction applied. Ex: [("ExampleError", "ExampleCorrection")]

        """

        # some error_handlers run while the shelltask is running. These are known as
        # Monitors and are labled via the is_monitor attribute. It's good for us
        # to separate these out from other error_handlers.
        self.monitors = [
            handler for handler in self.error_handlers if handler.is_monitor
        ]

        # We start with zero corrections that we slowly add to. This can be
        # thought of as a table with headers of...
        #   ("applied_errorhandler", "correction_applied")
        # NOTE: I took out the table headers and may add them back in
        corrections = []

        # ------ start of main while loop ------

        # we can try running the shelltask up to max_corrections. Because only one
        # correction is applied per attempt, you can view this as the maximum
        # number of attempts made on the calculation.
        while len(corrections) <= self.max_corrections:

            # launch the shelltask without waiting for it to complete. Also,
            # make sure to use common shell commands and to set the working
            # directory.
            # The preexec_fn keyword allows us to properly terminate jobs that
            # are launched with parallel processes (such as mpirun). This assigns
            # a parent id to it that we use when killing a job (if an error
            # handler calls for us to do so). This isn't possible on Windows though.
            # Stderr keyword indicates that we should capture the error if one
            # occurs so that we can report it to the user.
            process = subprocess.Popen(
                command,
                cwd=directory,
                shell=True,
                preexec_fn=None if platform.system() == "Windows" else os.setsid,
                stderr=subprocess.PIPE,
            )

            # Assume the shelltask has no errors until proven otherwise
            has_error = False

            # If monitor=True, then we want to supervise this shelltask as it
            # runs. If montors=[m1,m2,...], then we have monitors in place to actually
            # perform the monitoring. If both of these cases are true, then we
            # want to go through the error_handlers to check for errors until
            # the shelltask completes.
            if self.monitor and self.monitors:

                # ------ start of monitor while loop ------

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
                    if process.poll() is not None:
                        break
                    # check whether we should run monitors on this poll loop
                    if monitor_freq_n % self.monitor_freq == 0:
                        # iterate through each monitor
                        for error_handler in self.monitors:
                            # check if there's an error with this error_handler
                            # and grab the error if so
                            error = error_handler.check(directory)
                            if error:
                                # determine if it is_terminating
                                if error_handler.is_terminating:
                                    # If so, we kill the process but don't apply
                                    # the fix quite yet. That step is done below.
                                    self._terminate_job(process, command)
                                # Otherwise apply the fix and let the shelltask end
                                # naturally. An example of this is for codes
                                # where you add a STOP file to get it to
                                # finish rather than just killing the process.
                                # This is the special case error_handler that I talk
                                # about in my notes, where we really want to
                                # end the shelltask right away.
                                else:
                                    # apply the fix now
                                    correction = error_handler.correct(directory)
                                    # record what's been changed
                                    corrections.append((error_handler.name, correction))
                                # there's no need to look at the other monitors
                                # so break from the for-loop. We also don't
                                # need to monitor the stagedtask anymore since we just
                                # terminated it or signaled for its graceful
                                # end. So update the while-loop condition.
                                has_error = True
                                break
                # ------ end of monitor while loop ------
            # Now just wait for the process to finish. Note we use communicate
            # instead of the .wait() method. This is the recommended method
            # when we have stderr=subprocess.PIPE, which we use above.
            output, errors = process.communicate()
            # check if the return code is non-zero and thus failed.
            # The 'not has_error' is because terminate() will give a nonzero
            # when a monitor is triggered. We don't want to raise that
            # exception here but instead let the monitor handle that
            # error in the code below.
            if process.returncode != 0 and not has_error:
                # convert the error from bytes to a string
                errors = errors.decode("utf-8")
                # and report the error to the user
                raise NonZeroExitError(
                    f"The command ({command}) failed. The error output was...\n {errors}"
                )
            # Check for errors again, because a non-monitor may be higher
            # priority than the monitor triggered above (if there was one).
            # Since the error_handlers are in order of priority, only the first
            # will actually be applied and then we can retry the calc.
            for error_handler in self.error_handlers:

                # NOTE - The following special case is handled above:
                #   error_handler.is_monitor and not error_handler.is_terminating
                # BUG: I can see this being a source of bugs in the process so I
                # need to reconsider subclassing this special case. For now,
                # users should have this case at the lowest priority.

                # check if there's an error with this error_handler and grab the
                # error if there is one
                error = error_handler.check(directory)
                if error:
                    # record the error in case it wasn't done so above
                    has_error = True
                    # And apply the proper correction if there is one.
                    # Some error_handlers will even raise an error here signaling
                    # that the stagedtask is unrecoverable and a lost cause.
                    correction = error_handler.correct(directory)
                    # record what's been changed
                    corrections.append((error_handler.name, correction))
                    # break from the error_handler for-loop as we only apply the
                    # highest priority fix and nothing else.
                    break
            # write the log of corrections to file if requested. This is written
            # as a CSV file format and done every while-loop cycle because it
            # lets the user monitor the calculation and error handlers applied
            # as it goes. If no corrections were applied, we skip writing the file.
            if self.save_corrections_to_file and corrections:
                # compile the corrections metadata into a dataframe
                data = pandas.DataFrame(
                    corrections,
                    columns=["error_handler", "correction_applied"],
                )
                # write the dataframe to a csv file
                data.to_csv(
                    os.path.join(directory, self.corrections_filename),
                    index=False,
                )
            # now that we've gone through the error_handlers, let's see if any
            # non-terminating errors were found (terminating ones would raise
            # an error above). If there are no errors, we've finished the
            # calculation and can exit the while loop. Otherwise, just leave
            # everything where it's at and restart the while-loop with a new
            # attempt
            if not has_error:
                # break the while-loop
                break
        # ------ end of main while loop ------

        # make sure the while loop didn't exit because of the correction limit
        if len(corrections) >= self.max_corrections:
            raise MaxCorrectionsError(
                "The number of maximum corrections has been exceeded. Note the final "
                "error and its fix are still listed in the corrections file, but it "
                "was never used."
            )
        # now return the corrections for them to stored/used elsewhere
        return corrections

    @staticmethod
    def _terminate_job(process: subprocess.Popen, command: str):
        """
        Stopping the command we submitted can be a tricky business if we are running
        scripts in parallel (such as using mpirun). Different computers and OSs
        can require a different 'kill' command so we establish this separate
        method that can be overwritten.

        If you know your command needs a special case to kill all of its spawn
        processes, you can overwrite this method as well.

        Users should never call this directly becuase this is instead applied
        within the execute() method.

        Parameters
        ----------
        - `process`:
            The process object that will be terminated.
        - `command`:
            the command used to launch the process. This is sometimes useful
            when searching for all running processes under this name.
        """

        # The operating system (Windows, OSX, or Linux) will give us the best guess
        # as to where to access the blender command. The results are as you'd expect
        # except for Macs, which return "Darwin".
        #   Linux: Linux
        #   Mac: Darwin
        #   Windows: Windows
        operating_system = platform.system()

        # The normal line to end a popen process is just...
        #   process.terminate()
        # However this struggles to kill all "child" processes if we are using
        # something like mpirun to run things in parallel. Instead, we use the
        # os module to grab the parent id and send that the termination signal,
        # which # is also passed on to all child processes.
        # This command also doesn not work on windows, so I need to address this
        # as well.
        if operating_system != "Windows":
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        # note: SIGTERM is the normal signal but I use SIGKILL to try to address
        # permission errors.
        else:
            process.terminate()

        # As an example of an alternative approach to killing a job, here is
        # what Custodian (Materials Project) tries when killing a VASP job
        # submitted through mpirun:
        # try:
        #     os.system("killall vasp")
        # except Exception:
        #     pass

        # TODO: make it so terminate scripts can be loaded from the user's config
        # directory, which will make it so they don't have to overwrite all the
        # classes that inherit from this one.

    def workup(self, directory: str):
        """
        This method is called at the end of a job, *after* error detection.
        This allows post-processing, such as cleanup, analysis of results,
        etc. This should return the result of the entire job, such as a
        the final structure or final energy calculated.

        You should never call this method directly unless you are debugging. This
        is becuase workup() is normally called within the run() method.

        Some tasks don't require a workup() method, so by default, this method
        does nothing but "pass".

        Parameters
        ----------
        - `directory`:
            The directory to run everything in.

        """
        # Be sure to include directory (or **kwargs) as input argument for
        # higher-level compatibility with the run method and SupervisedStagedTask
        # You should never need to call this method directly!
        pass

    @defaults_from_attrs("command")
    def run(
        self,
        structure: Structure = None,
        directory: str = None,
        command: str = None,
        **kwargs,
    ):
        """
        Runs the entire staged task (setup, execution, workup), which includes
        supervising during execution.

        Call this method once you have your task initialized. For each run you
        can provide a new structure, directory, or command. For example,

        ``` python
        from simmate.calculator.example.tasks import ExampleTask

        my_task = ExampleTask()
        my_result = my_task.run(structure=my_structure, command=my_command)
        ```

        Parameters
        ----------
        - `structure`:
            The structure to use for the task, if one is required.
        - `command`:
            The command that will be called during execution.
        - `directory`:
            The directory to run everything in. This is passed to the ulitities
            function simmate.ulitities.get_directory
        - `**kwargs`:
            Any extra keywords that should be passed to the setup() method.

        Returns
        -------
        - a dictionary of the result, corrections, and working directory used
        for this task run

        """

        # because the command is something that is frequently changed at the
        # workflow level, then we want to make it so the user can set it for
        # each unique task.run() call. Otherwise we grab the default from the
        # class attribute

        # make sure a structure was given if it's required
        if not structure and self.requires_structure:
            raise StructureRequiredError("a structure is required as an input")
        # establish the working directory
        directory = get_directory(directory)

        # run the setup stage of the task
        self.setup(structure, directory, **kwargs)

        # run the shelltask and error supervision stages. This method returns
        # a list of any corrections applied during the run.
        corrections = self.execute(directory, command)

        # run the workup stage of the task. This is where the data/info is pull
        # out from the calculation and is thus our "result".
        result = self.workup(directory)

        # if requested, compresses the directory to a zip file and then removes
        # the directory.
        if self.compress_output:
            make_archive(directory)
        # Return our final information as a dictionary
        return {
            "result": result,
            "corrections": corrections,
            "directory": directory,
            "prefect_flow_run_id": prefect.context.flow_run_id
            if hasattr(prefect.context, "flow_run_id")
            else None,  # when not ran within a prefect flow, there won't be an id
        }

    @classmethod
    def get_config(cls):
        """
        Grabs the overall settings from the class.

        By default, this will just grab the class's __dict__ attribute but this
        can be overwritten to show only relevent information.
        """
        return dict(cls.__dict__)

    @classmethod
    def print_config(cls):
        """
        Takes the result of get_config and prints it in a yaml format that is
        easier to read.
        """
        config = cls.get_config()
        print(yaml.dump(config))


# Custom errors that indicate exactly what causes the S3Task to exit.


class MaxCorrectionsError(Exception):
    pass


class NonZeroExitError(Exception):
    pass


class StructureRequiredError(Exception):
    pass
