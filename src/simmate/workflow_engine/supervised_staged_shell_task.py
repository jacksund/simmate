# -*- coding: utf-8 -*-

"""
# The Supervised-Staged-Shell Task (aka "S3Task")

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
using the `run` method. You rarely use this class directly. Instead,
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
functionality of `pymatgen.io.vasp.sets` too. By merging all of these together
into one class, we make things much easier for users and creating new Tasks.


# Building a custom S3task

This class is commonly used to make tasks for our calculator modules, so you
will likely want to subclass this. Here is a basic example of inheriting
and then running a task:

``` python

from simmate.workflow_engine import S3Task
from example.error_handlers import PossibleError1, PossibleError2


class ExampleTask(SSSTask):

    command = "echo example"  # just prints out "example"
    
    # settings for error handling
    max_corrections = 7
    error_handlers = [PossibleError1, PossibleError2]
    polling_timestep = 0.1
    monitor_freq = 10
    
    # custom attributes
    some_new_setting = 123

    @classmethod
    def setup(cls, directory, custom_parmeter, **kwargs):
        print("I'm setting things up!")
        print(f"My new setting value is {cls.some_new_setting}")
        print(f"My new parameter value is {custom_parmeter}")

    @staticmethod
    def workup(directory):
        print("I'm working things up!")


task = ExampleTask()
result = task.run()
```

There are a two important things to note here:

1. It's optional to write new `setup` or `workup` methods. But if you do...
    - Both `setup` and `workup` method should be either a staticmethod or classmethod
    - Custom `setup` methods require the `directory` and `**kwargs` input parameters.
    - Custom `workup` methods require the `directory` input paramter
2. It's optional to set/overwrite attributes. You can also add new ones too.

For a full (and advanced) example, of a subclass take a look at
`simmate.calculators.vasp.tasks.base.VaspTask` and the tasks that use it like
`simmate.calculators.vasp.tasks.relaxation.matproj`.
"""

import os
import platform
import time
import signal
import subprocess
import yaml
from typing import List, Tuple
from functools import cache

import pandas

from prefect.tasks import Task
from prefect.context import get_run_context, MissingContextError

from simmate.workflow_engine import ErrorHandler
from simmate.utilities import get_directory, make_archive, make_error_archive

# cleanup_on_fail=False, # TODO I should add a Prefect state_handler that can
# reset the working directory between task retries -- in some cases we may
# want to delete the entire directory.

# OPTIMIZE: I think this class would greatly benefit from asyncio so that we
# know exactly when a shelltask completes, rather than looping and checking every
# set timestep.
# https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.create_subprocess_exec


class S3Task:
    """
    The base Supervised-Staged-Shell that many tasks inherit from. This class
    encapulates logic for running external programs (like VASP), fixing common
    errors during a calculation, and working up the results.
    """

    # I set this here so that I don't have to copy/paste the init method
    # every time I inherit from this class and want to update the default
    # command to use for the child class.
    command: str = None
    """
    The defualt shell command to use.
    """

    required_files = []
    """
    Before the command is executed, this list of files should be present
    in the working directory. This check will be made after `setup` is called
    and before `execute` is called. By default, no input files are required.
    """

    error_handlers: List[ErrorHandler] = []
    """
    A list of ErrorHandler objects to use in order of priority (that is, highest
    priority is first). If one handler is triggered, the correction will be 
    applied and none of the following handlers will be checked.
    """

    max_corrections: int = 10
    """
    The maximum number of times we can apply a correction and retry the shell
    command. The maximum number of times that corrections will be made (and
    shell command reran) before giving up on the calculation. Note, once this
    limit is exceeded, the error is stored without correcting or restarting
    the run.
    """

    monitor: bool = True
    """
    Whether to run monitor handlers while the command runs. False means
    wait until the job has completed.
    """

    polling_timestep: float = 1
    """
    If we are monitoring the job for errors while it runs, this is how often
    (in seconds) we should check the status of our job. Note this check is
    just whether the job is done or not. This is NOT how often we check for
    errors. See monitor_freq for that.
    """

    monitor_freq: int = 300
    """
    The frequency we should run check for errors with our monitors. This is
    based on the polling_timestep loops. For example, if we have a
    polling_timestep of 10 seconds and a monitor_freq of 2, then we would run
    the monitor checks every other loop -- or every 2x10 = 20 seconds. The
    default values of polling_timestep=10 and monitor_freq=30 indicate that
    we run monitoring functions every 5 minutes (10x30=300s=5min).
    """

    save_corrections_to_file: bool = True
    """
    Whether to write a log file of the corrections made. The default is True.
    """

    compress_output: bool = False
    """
    Whether to compress the directory to a zip file at the end of the
    task run. After compression, it will also delete the directory.
    The default is False.
    """

    @staticmethod
    def setup(directory: str, **kwargs):
        """
        This abstract method is ran before the command is actually executed. This
        allows for some pre-processing, such as writing input files or any other
        analysis.

        When writing a custom S3Task, you can overwrite this method. The only
        criteria is that you...

        1. include `directory` as the 1st input parameter and add `**kwargs`
        2. decorate your method with `@staticmethod` or `@classmethod`

        These criteria allow for compatibility with higher-level functinality.

        You should never call this method directly unless you are debugging. This
        is becuase `setup` is normally called within the `run` method.

        Some tasks don't require a `setup` method, so by default, this method
        does nothing but "pass".

        #### Parameters

        - `directory`:
            The directory to run everything in. Must exist already.

        - `**kwargs`:
            Extra kwargs that may be passed to some function within. Because
            Simmate prefers fixed settings for their workflows, this is typically
            not used, but instead, keywords should be explicitly defined when
            writing a setup method.
        """
        pass

    @classmethod
    def setup_restart(directory: str, **kwargs):
        """
        This method is used instead of `setup` when is_restart=True is passed
        to the run/run_config methods.

        This abstract method is ran before the command is actually executed. This
        allows for some pre-processing, such as writing input files or any other
        analysis.

        When writing a custom S3Task, you can overwrite this method. The only
        criteria is that you...

        1. include `directory` as the 1st input parameter and add `**kwargs`
        2. decorate your method with `@staticmethod` or `@classmethod`

        These criteria allow for compatibility with higher-level functinality.

        You should never call this method directly unless you are debugging. This
        is becuase `setup_restart` is normally called within the `run` method.

        Some tasks don't require a `setup_restart` method, so by default, this
        method does nothing but "pass".

        #### Parameters

        - `directory`:
            The directory to run everything in. Must exist already.

        - `**kwargs`:
            Extra kwargs that may be passed to some function within. Because
            Simmate prefers fixed settings for their workflows, this is typically
            not used, but instead, keywords should be explicitly defined when
            writing a setup method.
        """
        pass

    @classmethod
    def _check_input_files(cls, directory: str, raise_if_missing: bool = True):
        """
        Make sure that there are the proper input files to run this calc
        """

        filenames = [os.path.join(directory, file) for file in cls.required_files]
        if not all(os.path.exists(filename) for filename in filenames):
            if raise_if_missing:
                raise Exception(
                    "Make sure your `setup` method directory source is set up correctly"
                    "The following files must exist in the directory where "
                    f"this task is ran but some are missing: {cls.required_files}"
                )
            return False  # indicates something is missing
        return True  # indicates all files are present

    @classmethod
    def execute(cls, directory: str, command: str) -> List[Tuple[str]]:
        """
        This calls the command within the target directory and handles all error
        handling as well as monitoring of the job.

        You should never call this method directly unless you are debugging. This
        is becuase `execute` is normally called within the `run` method.

        Some tasks don't require a setup() method, so by default, this method
        does nothing but "pass".

        #### Parameters

        - `directory`:
            The directory to run everything in.
        - `command`:
            The command that will be called during execution.

        #### Returns

        - `corrections`
            A list of tuples where each entry is a error identified and the
            correction applied. Ex: [("ExampleError", "ExampleCorrection")]

        """

        # some error_handlers run while the shelltask is running. These are known as
        # Monitors and are labled via the is_monitor attribute. It's good for us
        # to separate these out from other error_handlers.
        cls.monitors = [handler for handler in cls.error_handlers if handler.is_monitor]

        # in case this is a restarted calculation, check if there is a list
        # of corrections in the current directory and load those as the start point
        corrections_filename = os.path.join(directory, "simmate_corrections.csv")
        if os.path.exists(corrections_filename):
            data = pandas.read_csv(corrections_filename)
            corrections = data.values.tolist()
        # Otherwise we start with zero corrections that we slowly add to. This
        # can be thought of as a table with headers of...
        #   ("applied_errorhandler", "correction_applied")
        else:
            corrections = []

        # ------ start of main while loop ------

        # we can try running the shelltask up to max_corrections. Because only one
        # correction is applied per attempt, you can view this as the maximum
        # number of attempts made on the calculation.
        while len(corrections) <= cls.max_corrections:

            # launch the shelltask without waiting for it to complete. Also,
            # make sure to use common shell commands and to set the working
            # directory.
            #
            # Stderr keyword indicates that we should capture the error if one
            # occurs so that we can report it to the user.
            #
            # The preexec_fn keyword allows us to properly terminate jobs that
            # are launched with parallel processes (such as mpirun). This assigns
            # a parent id to it that we use when killing a job (if an error
            # handler calls for us to do so). This isn't possible on Windows though.
            #
            # OPTIMIZE / BUG: preexec_fn adds about 0.02s overhead to the calculation
            # so we may not want to always use it... Instead we could try to only
            # use it when the command includes "mpirun". Though this may introduce
            # a bug if another is another parallel command used besides mpirun.
            # An example of this might be deepmd which automatically submits
            # things in parallel without calling mpirun up-front.
            process = subprocess.Popen(
                command,
                cwd=directory,
                shell=True,
                preexec_fn=None if platform.system() == "Windows"
                # or "mpirun" not in command  # See bug/optimize comment above
                else os.setsid,
                stderr=subprocess.PIPE,
            )

            # Assume the shelltask has no errors and can retry until proven otherwise
            has_error = False
            allow_retry = True

            # If monitor=True, then we want to supervise this shelltask as it
            # runs. If montors=[m1,m2,...], then we have monitors in place to actually
            # perform the monitoring. If both of these cases are true, then we
            # want to go through the error_handlers to check for errors until
            # the shelltask completes.
            if cls.monitor and cls.monitors:

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
                    time.sleep(cls.polling_timestep)

                    # check if the shelltasks is complete. poll will return 0
                    # when it's done, in which case we break the loop
                    if process.poll() is not None:
                        break
                    # check whether we should run monitors on this poll loop
                    if monitor_freq_n % cls.monitor_freq == 0:
                        # iterate through each monitor
                        for error_handler in cls.monitors:
                            # check if there's an error with this error_handler
                            # and grab the error if so
                            error = error_handler.check(directory)
                            if error:
                                # determine if the error handler has a
                                # custom termination method. If not, use our
                                # default one from this class.
                                # The "allow_retry" tells us whether we should
                                # end the job even if we still have an error.
                                # For example, our Walltime handler will tell
                                # us to shutdown and not try anymore -- but
                                # it won't raise an error in order to allow
                                # our workup to run.
                                if not error_handler.has_custom_termination:
                                    # If so, we kill the process but don't apply
                                    # the fix quite yet. That step is done below.
                                    allow_retry = cls._terminate_job(
                                        directory=directory,
                                        process=process,
                                        command=command,
                                    )

                                # Otherwise use the custom termination. An
                                # example of this is for codes where you add
                                # a STOP file to get it to finish rather than
                                # just killing the process. We use this feature
                                # in our VASP Walltime handler.
                                else:
                                    allow_retry = error_handler.terminate_job(
                                        directory=directory,
                                        process=process,
                                        command=command,
                                    )
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
            for error_handler in cls.error_handlers:

                # check if there's an error with this error_handler and grab the
                # error if there is one
                error = error_handler.check(directory)
                if error:
                    # record the error in case it wasn't done so above
                    has_error = True
                    # make a copy of the directory contents and
                    # store as an archive within the same directory
                    make_error_archive(directory)
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
            if cls.save_corrections_to_file and corrections:
                # compile the corrections metadata into a dataframe
                data = pandas.DataFrame(
                    corrections,
                    columns=["error_handler", "correction_applied"],
                )
                # write the dataframe to a csv file
                data.to_csv(corrections_filename, index=False)

            # If there are no errors, we've finished the calculation and can
            # exit the while loop. Alternatively, some "soft" errors (such as
            # Walltimes) signal us to finish even though there's technically
            # a problem -- they do this will allow_retry=False. Otherwise,
            # just leave everything where it's at and restart the
            # while-loop with a new attempt.
            if not has_error or not allow_retry:
                # break the while-loop
                break

        # ------ end of main while loop ------

        # make sure the while loop didn't exit because of the correction limit
        if len(corrections) >= cls.max_corrections:
            raise MaxCorrectionsError(
                "The number of maximum corrections has been exceeded. Note the final "
                "error and its fix are still listed in the corrections file, but it "
                "was never used."
            )
        # now return the corrections for them to stored/used elsewhere
        return corrections

    @staticmethod
    def _terminate_job(directory: str, process: subprocess.Popen, command: str):
        """
        Stopping the command we submitted can be a tricky business if we are running
        scripts in parallel (such as using mpirun). Different computers and OSs
        can require a different 'kill' command so we establish this separate
        method that can be overwritten.

        If you know your command needs a special case to kill all of its spawn
        processes, you can overwrite this method as well.

        Users should never call this directly becuase this is instead applied
        within the execute() method.

        #### Parameters

        - `directory`:
            The base directory the calculation is taking place in.

        - `process`:
            The process object that will be terminated.

        - `command`:
            the command used to launch the process. This is sometimes useful
            when searching for all running processes under this name.

        #### Returns

        - `allow_retry`:
            if the job should be attempted again when there is a possible fix
            from the correct() method. Defaults to True. In the case where
            allow_retry=False and correct() does NOT raise an error, the
            workup methods will still be called - despite the calculation
            technically having an error.
        """

        # The operating system (Windows, OSX, or Linux) will give us the best guess
        # as to where to access the running command. The results are as you'd expect
        # except for Macs, which returns "Darwin".
        #   Linux: Linux
        #   Mac: Darwin
        #   Windows: Windows
        operating_system = platform.system()

        # The normal line to end a popen process is just...
        #   process.terminate()
        # However this struggles to kill all "child" processes if we are using
        # something like mpirun to run things in parallel. Instead, we use the
        # os module to grab the parent id and send that the termination signal,
        # which is also passed on to all child processes.
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

        # By default, termination allows for restarts, so we return a
        # "allow_retry" value of True.
        return True

    @staticmethod
    def workup(directory: str):
        """
        This method is called at the end of a job, *after* error detection.
        This allows post-processing, such as cleanup, analysis of results,
        etc. This should return the result of the entire job, such as a
        the final structure or final energy calculated.

        When writing a custom S3Task, you can overwrite this method. The only
        criteria is that you...

        1. include `directory` as an input parameters
        2. decorate your method with `@staticmethod` or `@classmethod`

        These criteria allow for compatibility with higher-level functinality.

        You should never call this method directly unless you are debugging. This
        is becuase `workup` is normally called within the `run` method.

        Some tasks don't require a `workup` method, so by default, this method
        doesn't nothing but "pass".

        #### Parameters

        - `directory`:
            The directory to run everything in.
        """
        pass

    @classmethod
    def run_config(
        cls,
        directory: str = None,
        command: str = None,
        is_restart: bool = False,
        **kwargs,
    ):
        """
         Runs the entire staged task (setup, execution, workup), which includes
         supervising during execution.

         Call this method once you have your task initialized. For each run you
         can provide a new structure, directory, or command. For example:

         ``` python
         from simmate.calculator.example.tasks import ExampleTask

         my_result = ExampleTask.run(command=my_command)
         ```

         #### Parameters

         - `command`:
             The command that will be called during execution.

         - `directory`:
             The directory to run everything in. This is passed to the ulitities
             function simmate.ulitities.get_directory

        - `is_restart`:
            whether or not this calculation is a continuation of a previous run
            (i.e. a restarted calculation). If so, the `setup_restart` will be
            called instead of the setup method. Extra checks will be made to
            see if the calculation completed already too.

         - `**kwargs`:
             Any extra keywords that should be passed to the setup() method.

        #### Returns

         - a dictionary of the result, corrections, and working directory used
         for this task run
        """

        # because the command is something that is frequently changed at the
        # workflow level, then we want to make it so the user can set it for
        # each unique task.run() call. Otherwise we grab the default from the
        # class attribute
        if not command:
            command = cls.command

        # establish the working directory
        directory = get_directory(directory)

        # When handling restarted calculations, we check for the final summary
        # file and if it exists, we know the calculation has already completed
        # (and therefore doesn't require a restart). This helps handle nested
        # workflows where we don't know which task to restart at.
        summary_filename = os.path.join(directory, "simmate_summary.yaml")
        is_complete = os.path.exists(summary_filename)
        is_dir_setup = cls._check_input_files(directory, raise_if_missing=False)

        # run the setup stage of the task, where there is a unique method
        # if we are picking up from a previously paused run.
        if (not is_restart and not is_complete) or not is_dir_setup:
            cls.setup(directory=directory, **kwargs)
        elif is_restart and not is_complete:
            cls.setup_restart(directory=directory, **kwargs)
        else:
            print("Calculation is already completed. Skipping setup.")

        # now if we have a restart OR have an incomplete calculation that is being
        # restarted, we can check our files and run the external program
        if not is_restart or not is_complete:

            # make sure proper files are present
            cls._check_input_files(directory)

            # run the shelltask and error supervision stages. This method returns
            # a list of any corrections applied during the run.
            corrections = cls.execute(directory, command)
        else:
            print("Calculation is already completed. Skipping execution.")

            # load the corrections from file for reference
            corrections_filename = os.path.join(directory, "simmate_corrections.csv")
            if os.path.exists(corrections_filename):
                data = pandas.read_csv(corrections_filename)
                corrections = data.values.tolist()
            else:
                corrections = []
            # OPTIMIZE: this same code is at the start of the execute method.
            # Consider making it into a utility.

        # run the workup stage of the task. This is where the data/info is pulled
        # out from the calculation and is thus our "result".
        result = cls.workup(directory=directory)

        # if requested, compresses the directory to a zip file and then removes
        # the directory.
        if cls.compress_output:
            make_archive(directory)

        # Grab the prefect flow run id. Note, when not ran within a prefect
        # flow, there won't be an id. We therefore need this try/except
        try:
            prefect_context = get_run_context()
            flow_run_id = str(prefect_context.task_run.flow_run_id)
        except MissingContextError:
            flow_run_id = None

        # Return our final information as a dictionary
        return {
            "result": result,
            "corrections": corrections,
            "directory": directory,
            "prefect_flow_run_id": flow_run_id,
        }

    @classmethod
    @cache
    def to_prefect_task(cls) -> Task:
        """
        Converts this Simmate s3task into a Prefect task
        """

        # Build the Task object directly instead of using prefect's @task decorator
        task = Task(
            fn=cls.run_config,
            name=cls.__name__,
        )

        # as an extra, we set this attribute to the prefect task instance, which
        # allows us to access the source Simmate S3Task easily with Prefect's
        # context managers.
        task.simmate_s3task = cls

        return task

    @classmethod
    def run(cls, **kwargs):
        """
        A convience method to run this task as a registered task in a prefect context.
        """
        task = cls.to_prefect_task()
        state = task.submit(**kwargs)

        # We don't want to block and wait because this might disable parallel
        # features of subflows. We therefore return the state and let the
        # user decide if/when to block.
        # result = state.result()

        return state

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
