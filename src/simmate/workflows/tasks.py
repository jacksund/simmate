# -*- coding: utf-8 -*-

"""

Prefect does have a built-in way to loop a certain task that I could use, but 
I think it's cleaner and more robust (plus I can run it locally) when I write
my own custom Task class. 

For how it would be done in Prefect, see their example here:
    https://docs.prefect.io/core/examples/task_looping.html

The organization of this class is largely a simplification of Custodian where
I am running a single job with the following steps...
- Write Input Files based on custom+defualt settings
- Run the calculation by calling the program 
- Load ouput files
- check for errors
- [correct them, rerun]
- postprocess/analysis

For a visual, it is the same as shown in this link except with only 1 job
rather than a list of jobs. I limit it to one because I believe multiple jobs
should be separate prefect tasks, not crammed into one task/job. Thus, there
is no "All jobs done?" step as shown in the image.
https://materialsproject.github.io/custodian/index.html#usage


Also, this is really a subclass of the Prefect Task to allow for monitoring
handlers. More specifically, we want to be able to run Handlers while the task
is also running via some executor (subprocess or Dask). Monitors are currently
for reading outputs files and I don't take into account accessing task local 
varaibles or even try to access those. Prefect already supports handlers when
the task changes state via the Task(state_handlers=[]) option.

Altogether, I should discuss with Prefect on monitor_handlers and being able
to use their LOOP method outside of the flow.run() -- specifcally it does not 
work for task.run()



The types of handlers if I split them up...
    monitor_handlers=(),
    state_handlers=(), # already done in the Prefect Task class
state_handlers includes custodian types Handler(monitor=False) and Validator



##### notes while rewriting Custodian #####

renamed some variables for clarity. 
The most signicant renaming that I'd like to do (but don't yet) is the 
Job.correct() method to Job.fix(), which is entirely based on my
personal preference.

written for a single job, not a list of jobs. The list of jobs should be 
specified at the Workflow level (higher level). Therefore run and _run_job 
methods are effectively merged.

Would it instead make sense to have checkpoint_input/output within 
the setup and workup/postprocess methods of the Job object?
checkpoint_input is only for the very start of the job (initial directory). If 
nothing works, we may want to recover the initial state of the directory.
checkpoint_output is for the end of the job. You'll want to use this instead
of checkpoint_input if there are multiple different tasks that follow it.
As a guide where each letter is a different supervised job:
    A-done
        its up to the user whether the final finals are compressed
    A-B
        A and B have only input compressed but not output
        or... 
        A and B have only output compressed but not input
    A-[B,C,D]
        A has output compressed and [B,C,D] do not use compressed input as
        that would give rise to duplicate compressed files
    [A,B,C]-D
        D has input compressed which is a combination of [A,B,C] outputs
    [A,B,C]-[D,E,F]
        depends... compressing outputs would be safest bet
    When in doubt, compress both input and output! Setting either to False
    is really just a way to save time and disk space.

no terminate_func option. Assumes the job's future has a cancel method which 
follows the concurrent.futures convention

scratch_dir option is moved to run method to allow this task instance to be
ran in parallel if desired. Each invidual task run may want a different working
directory


SupervisedShellTask is a combination of:

    prefect.tasks.shell.ShellTask 
    https://github.com/PrefectHQ/prefect/blob/master/src/prefect/tasks/shell.py
    
    custodian.custodian.Custodian
    https://github.com/materialsproject/custodian/blob/master/custodian/custodian.py

Guide on contributing a new task to Prefect:
    https://docs.prefect.io/core/task_library/contributing.html#task-structure

skip_handler_errors is removed and the error is always raised. If you don't 
want it raised, then that should be done inside of the Handler class itself.

monitors have the is_terminating option, which is really only used when we want
to stop vasp naturally at the end of an ionic step using the STOPCAR. Further,
we have a priority of Handlers where only the first is used. If this is the 
special case, it will prevent a lower priority one from making the fix. These
special cases cause for extra messy code so I wonder if there's a better way
to handle this, such as a different subclass of Handler. I don't do anything
extra at the moment and just add the extra code.

The Job class has a terminate method, but I only ever see it used in one case
which is VASP's constrained_opt_run. I'm not sure what's happening here, but 
I don't think this merits an added method for all Jobs. Perhaps this special
termination should instead happen in the Job's postprocessing method.

Custodian's Validator class is when the is_monitor=False and the correct() 
method simply passes. Also based on Custodian, they only run them at the end
of the a job (that is all handlers passed). Thus their third characteristic
is that the are the lowest priority handlers. Because I am able to define a
Validator completely in the context of a Handlers list, I choose to remove
the validators input to avoid confusion. This does open validators up to being
missused by beginners (by putting one before the a Handle), which might be why 
they chose to separate them. I will therefore make one change to such 
Validators in that their hidden correct() method is not just a pass, but 
actually raises and error immediately. If you don't want it raised, see my 
comment on why skip_handler_errors was removed.

I still need to work in working directory (and tempdir) settings as well as 
where to saved the compresse output file

"""

import os
import time
from shutil import make_archive
from subprocess import Popen
from tempfile import TemporaryDirectory

from prefect import Task
from prefect.utilities.tasks import defaults_from_attrs

#!!! I expect dir to be an input arg for job.run(dir=None), so I should pass
#!!! that through. I need to consider possible overwriting but that may be
#!!! fine based on priority.
class SupervisedJobTask(Task):
    def __init__(
        self,
        # core parts
        job,
        handlers=(),
        dir=None,
        # return, cleanup, and file saving settings
        compress_output=False,
        return_corrections=True,
        save_corrections_tofile=True,
        corrections_filename="simmate_corrections_log.txt",
        # settings for the job supervision
        max_corrections=5,
        polling_timestep=10,
        monitor_freq=30,
        # To support other Prefect input options
        **kwargs,
    ):

        # save input values for reference
        self.job = job
        self.handlers = handlers
        self.dir = dir

        self.max_corrections = max_corrections
        self.polling_timestep = polling_timestep
        self.monitor_freq = monitor_freq

        self.compress_output = compress_output
        self.return_corrections = return_corrections
        self.save_corrections_tofile = save_corrections_tofile
        self.corrections_filename = corrections_filename

        # some handlers run while the job is running. These are known as
        # Monitors and are labled via the is_monitor attribute.
        self.monitors = [h for h in handlers if h.is_monitor]

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    @defaults_from_attrs("job", "dir")
    def run(self, job, dir=None):

        # Establish the working directory for this run.
        # if no directory was provided, use the current working directory
        if not dir:
            dir = os.getcwd()
        # if the user provided a tempdir, we want it's name
        elif isinstance(dir, TemporaryDirectory):
            dir = dir.name
        # otherwise make sure the directory the user provided exists
        else:
            os.path.exists(dir)

        # run the initial job setup
        job.setup()

        # We start with zero corrections (empty list) that we slowly add to.
        corrections = []

        # we can try running the job up to max_corrections. Because only one
        # correction is applied per attempt, you can view this as the maximum
        # number of attempts made on the calculation.
        while len(corrections) < self.max_corrections:

            # launch the job
            #!!! Am I able to do this in an asyncio mode? Because this is a
            # prefect task that is launched through an Executor, it is likely
            # this is running on a single thread worker -- so I'm not sure
            # that asyncio will work here... If I am able to do that, I should
            # move this launch to a Job class method (job.run_aysnc)
            future = job.run()
            # check that the future is a from subprocess.Popen subprocess
            # Popen returns a __ instead of waiting like subprocess.run()
            is_popen = isinstance(future, Popen)

            # Assume the job has no errors until proven otherwise
            has_error = False

            # Go through the handlers to check for errors until the future
            # completes
            # Only does this if future is an instance of subprocess.Popen
            #!!! elif it is a Dask future or Conncurrent future # TO-DO
            #!!! I would want to run this in async mode so I know exactly when
            #!!! the future completes though.
            # if there aren't any monitors, just wait for the subprocess
            # otherwise loop through the monitors until the job completes
            if self.monitors and is_popen:
                # We want to loop until we find an error and keep track of
                # which loops to run the monitor function on because we don't
                # want them to run nonstop. This variable allows us to
                # every Nth loop.
                monitor_freq_n = 0
                while not has_error:
                    monitor_freq_n += 1
                    # Sleep the set amount before checking the job status
                    time.sleep(self.polling_time_step)

                    # check if the jobs is complete. poll will return 0
                    # when it's done, in which case we break the loop
                    if has_error or future.poll() is not None:
                        break

                    # check whether we should run monitors on this poll loop
                    if monitor_freq_n % self.monitor_freq == 0:
                        # iterate through each monitor
                        for handler in self.monitors:
                            # check if there's an error with this handler
                            if handler.check():

                                # determine if it is_terminating
                                if handler.is_terminating:
                                    # kill the process but don't apply the fix
                                    # quite yet. See below for more on this.
                                    future.terminate()
                                # Otherwise apply the fix and let the job end
                                # naturally. An example of this is for codes
                                # where you add a STOP file to get it to
                                # finish rather than just killing the process.
                                # This is the special case Handler that I talk
                                # about in my notes, where we really want to
                                # end the job right away.
                                else:
                                    # apply the fix now
                                    correction = handler.correct()
                                    # record what's been changed
                                    corrections.append(correction)

                                # there's no need to look at the other monitors
                                # so break from the for-loop. We also don't
                                # need to monitor the job anymore since we just
                                # terminated it or signaled for its graceful
                                # end. So update the while-loop condition.
                                has_error = True
                                break

            # TO-DO: elif future from dask
            if is_popen:
                # Now just wait for the process to finish
                future.wait()
                # check if the return code is non-zero and
                if future.returncode != 0 and self.terminate_on_nonzero_returncode:
                    raise Exception  #!!! switch to a raising a custom error

            # Check for errors again, because a non-monitor may be higher
            # priority than the monitor triggered about (if there was one).
            # Since the handlers are in order of priority, only the first
            # will actually be applied and then we can retry the calc.
            for handler in self.handlers:

                # NOTE - The following special case is handled above:
                #   handler.is_monitor and not handler.is_terminating
                # I can see this being a source of bugs in the future so I
                # need to reconsider subclassing this special case.

                # check if there's an error with this handler
                if handler.check():
                    # record that the error in case it wasn't done so above
                    has_error = True
                    # And apply the proper correction if there is one.
                    # Some Handlers will even raise an error here signaling
                    # that the job is unrecoverable and a lost cause.
                    correction = handler.correct()
                    # record what's been changed
                    corrections.append(correction)
                    # break from the handler for-loop as we only apply the
                    # highest priority fix and nothing else.
                    break

            # now that we've gone through the handlers, let's see if any
            # non-terminating errors were found (terminating ones would raise
            # an error above). If there are no errors, we've finished the
            # calculation and can exit the while loop. Otherwise, just leave
            # everything where it's at and restart the while-loop with a new
            # attempt
            if not has_error:
                # break the while-loop
                break

        # run the postprocess, which should return the result
        result = job.postprocess()

        # write the log of corrections to file if requested
        if self.save_corrections_tofile:
            with open(self.corrections_filename, "w") as logfile:
                for correction in corrections:
                    logfile.write(f"{correction}\n")

        # compress the output directory for storage if requested
        if self.compress_output:
            make_archive(
                # full path to where to save the archive
                #!!! By default I choose within the current directory and save
                #!!! it as the same name of the directory. This will be a
                #!!! overwritten if I run another job right after it.
                #!!! Consider using a unique filename for each save and returning
                #!!! it, or just using a generic simmate_checkpoint name.
                base_name=os.path.join(os.path.abspath(dir), os.path.basename(dir)),
                # format to use switch to gztar after testing
                format="zip",
                # full path to up tp dir that will be archived
                root_dir=os.path.dirname(dir),
                # directory within root_dir to archive
                base_dir=os.path.basename(dir),
            )

        # Based on the input settings, return either the (result, log) or
        # just the result on its own.
        if self.return_corrections:
            return result, corrections
        else:
            return result


# -----------------------------------------------------------------------------
