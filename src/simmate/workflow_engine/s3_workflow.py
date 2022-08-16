# -*- coding: utf-8 -*-

"""
# The Supervised-Staged-Shell Workflow (aka "S3Workflow")

This class contains the core functionality to **supervise** a **staged** workflow
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
output files for common errors/issues -- even while the other program is still
running. If an error is found, we stop the program, fix the issue, and then 
restart it.


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

Running S3Workflows is the same as normal workflows (e.g. using the `run` method),
and this entire process of supervising, staging, and shell execution is done for you!


# S3Workflows for common Calculators

For programs that are commonly used in material science, you should check the
`simmate.calculators` module and then a given calculator's `workflow` module.
Many have a subclass of `S3Workflow` already built for you. For example, VASP
user can take advantage of the following class:
`simmate.calculators.vasp.workflows.base.VaspWorkflow`



# Building a custom S3Workflow

Before starting a custom `S3Workflow`, make sure you have read the section 
above this (on S3Workflows for common Calculators like VASP). You should also 
have gone through the guides on building a custom `Workflow`.

NOTE: Custom `S3Workflows` must also follow the naming conventions required
of `Workflow`s


## Simple command call

The most basic example of a S3Workflow is just calling some command -- without
doing anything else (no input files, no error handling, etc.). 

Unlike custom `Workflows` were we defined a `run_config` method, `S3Workflows`
have a pre-built `run_config` method that carries out the different stages and 
monitoring of a workflow for us. So all the work is already done for us!

As an example, let's just use the command `echo` to print something:
    
``` python

from simmate.workflow_engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    use_database = False  # we aren't using a custom table for now
    monitor = False  # there is no error handling yet
    command = "echo Hello"

# behaves like a normal workflow
state = Example__Echo__SayHello.run()
result = state.result()
```

IMPORTANT: Note that  we used "Echo" in our workflow name. This helps the user 
see what commands or programs will be called when a workflow is ran.


## Custom setup and workup

Now what if we'd like to write input files or read output files that are created?
Here, we need to update our `setup` and `workup` methods:

``` python

from simmate.workflow_engine import S3Workflow

class Example__Echo__SayHello(S3Workflow):
    
    use_database = False  # we aren't using a custom table for now
    monitor = False  # there is no error handling yet

    command = "echo Hello > output.txt"  # adds "Hello" into a new file

    @classmethod
    def setup(cls, directory, custom_parameter, **kwargs):
        # The directory given is a pathlib.Path object for the directory
        # that the command will be called in
        
        print("I'm setting things up!")
        print(f"My new setting value is {cls.some_new_setting}")
        print(f"My new parameter value is {custom_parmeter}")
        
        return  # no need to return anything. Nothing will be done with it.

    @staticmethod
    def workup(directory):
        # The directory given is a pathlib.Path object for the directory
        # that the command will be called in
        
        # Simply check that we have a new file
        output_file = directory / "output.txt"
        assert output_file.exists()
        
        print("I'm working things up!")
        return "Done!"

task = Example__Echo__SayHello()
result = task.run()
```

There are a two important things to note here:

1. It's optional to write new `setup` or `workup` methods. But if you do...
    - Both `setup` and `workup` method should be either a staticmethod or classmethod
    - Custom `setup` methods require the `directory` and `**kwargs` input parameters.
    - Custom `workup` methods require the `directory` input paramter
2. It's optional to set/overwrite attributes. You can also add new ones too.

Note: S3Workflows for a custom calculator (such `VaspWorkflow` for VASP)
will often have custom `setup` and `workup` methods already defined for you.
You can update/override these as you see fit.

For a full (and advanced) example of a subclass take a look at
`simmate.calculators.vasp.workflows.base.VaspWorkflow` and the tasks that use it like
`simmate.calculators.vasp.workflows.relaxation.matproj`.


# Custom error handling

See the documentation located at `simmate.workflow_engine.error_handler` for
more information.


# Continuation of workflows

This is an experimental feature and for advanced users only. (TODO)


# Alternatives

For experts, this class can be viewed as a combination of prefect's ShellTask,
a custodian Job, and Custodian monitoring. When subclassing this, we can absorb
functionality of `pymatgen.io.vasp.sets` too. By merging all of these together
into one class, we make things much easier for users and creating new Tasks.

"""

import logging
import os
import platform
import signal
import subprocess
import time
from pathlib import Path

import pandas

from simmate.utilities import get_directory, make_error_archive
from simmate.workflow_engine import ErrorHandler, Workflow


class S3Workflow(Workflow):
    """
    The base Supervised-Staged-Shell that many workflows inherit from. This class
    encapulates logic for running external programs (like VASP), fixing common
    errors during a calculation, and working up the results.
    """

    _parameter_methods = Workflow._parameter_methods + ["setup"]

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

    error_handlers: list[ErrorHandler] = []
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

    # cleanup_on_fail=False, # TODO I should add a Prefect state_handler that can
    # reset the working directory between task retries -- in some cases we may
    # want to delete the entire directory.

    # OPTIMIZE: I think this class would greatly benefit from asyncio so that we
    # know exactly when a shelltask completes, rather than looping and checking every
    # set timestep.
    # https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.create_subprocess_exec

    @classmethod
    def run_config(
        cls,
        directory: Path = None,
        command: str = None,
        is_restart: bool = False,
        **kwargs,
    ):
        """
         Runs the entire staged task (setup, execution, workup), which includes
         supervising during execution.

         #### Example use

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
        summary_filename = directory / "simmate_summary.yaml"
        is_complete = summary_filename.exists()
        is_dir_setup = cls._check_input_files(directory, raise_if_missing=False)

        # run the setup stage of the task, where there is a unique method
        # if we are picking up from a previously paused run.
        if (not is_restart and not is_complete) or not is_dir_setup:
            cls.setup(directory=directory, **kwargs)
        elif is_restart and not is_complete:
            cls.setup_restart(directory=directory, **kwargs)
        else:
            logging.info("Calculation is already completed. Skipping setup.")

        # now if we have a restart OR have an incomplete calculation that is being
        # restarted, we can check our files and run the external program
        if not is_restart or not is_complete:

            # make sure proper files are present
            cls._check_input_files(directory)

            # run the shelltask and error supervision stages. This method returns
            # a list of any corrections applied during the run.
            corrections = cls.execute(directory, command)
        else:
            logging.info("Calculation is already completed. Skipping execution.")

            # load the corrections from file for reference
            corrections_filename = directory / "simmate_corrections.csv"
            if corrections_filename.exists():
                data = pandas.read_csv(corrections_filename)
                corrections = data.values.tolist()
            else:
                corrections = []
            # OPTIMIZE: this same code is at the start of the execute method.
            # Consider making it into a utility.

        # run the workup stage of the task. This is where the data/info is pulled
        # out from the calculation and is thus our "result".
        result = cls.workup(directory=directory)

        # Return our final information as a dictionary
        result = {
            "result": result,
            "corrections": corrections,
            "directory": directory,
        }

        return result

    @staticmethod
    def setup(directory: Path, **kwargs):
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
    def setup_restart(directory: Path, **kwargs):
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
    def _check_input_files(cls, directory: Path, raise_if_missing: bool = True):
        """
        Make sure that there are the proper input files to run this calc
        """

        filenames = [directory / file for file in cls.required_files]
        if not all(filename.exists() for filename in filenames):
            if raise_if_missing:
                raise Exception(
                    "Make sure your `setup` method directory source is defined correctly"
                    "The following files must exist in the directory where "
                    f"this task is ran but some are missing: {cls.required_files}"
                )
            return False  # indicates something is missing
        return True  # indicates all files are present

    @classmethod
    def execute(cls, directory: Path, command: str) -> list[tuple[str]]:
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
        corrections_filename = directory / "simmate_corrections.csv"
        if corrections_filename.exists():
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
            logging.info(f"Using {directory}")
            logging.info(f"Running '{command}'")
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
                # and report the error to the user. Mac/Linux label this as exit
                # code 127, whereas windows doesn't so the message needs to be
                # read.
                if process.returncode == 127 or (
                    platform.system() == "Windows"
                    and "is not recognized as an internal or external command"
                ):
                    raise CommandNotFoundError(
                        f"The command ({command}) failed becauase it could not be found. "
                        "This typically means that either (a) you have not installed "
                        "the program required for this command or (b) you forgot to "
                        "call 'module load ...' before trying to start the program. "
                        f"The full error output was:\n\n {errors}"
                    )
                else:
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
                    logging.info(
                        f"Found error '{error_handler.name}'. Fixed with '{correction}'"
                    )
                    # break from the error_handler for-loop as we only apply the
                    # highest priority fix and nothing else.
                    break

            # write the log of corrections to file if there are any. This is written
            # as a CSV file format and done every while-loop cycle because it
            # lets the user monitor the calculation and error handlers applied
            # as it goes. If no corrections were applied, we skip writing the file.
            if corrections:
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
    def _terminate_job(directory: Path, process: subprocess.Popen, command: str):
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
    def workup(directory: Path):
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


# Custom errors that indicate exactly what causes the S3Task to exit.


class MaxCorrectionsError(Exception):
    pass


class NonZeroExitError(Exception):
    pass


class CommandNotFoundError(NonZeroExitError):
    pass
