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
want it raised, then that should be done inside of the Handler class itself. I
might want to ensure a log file is written before raising the error though.

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

Hanlders in Custodian save the errors to the class instance via self.errors and
therefore only return a boolean with the check() method. Instead, I write
Hanlders so that they support parallelization -- no single run saves to the
class instance, but it is instead returned. Therefore, errors are instead
return from the check() method and must be passed into the correct() method.
As an example, Custiadian you would do...
    has_error = handler.check()
    error_and_correction = handler.correct()
whereas with Simmate you would do...
    error = handler.check()
    correction = handler.correct(error)

For the Job abstract class, I should consider making Job a Prefect workflow
made of task components because writing inputs and postprocessing processes
are probably common accross all jobs of a given type (like VaspJobs). I'm
thinking that both SupervisedJobTask and Job can be Prefect Tasks where you
can pick which ones to make a task. Thus these would only be made of the run()
method and the Handlers. The workflow would look like...
SetupTask(s)-->ShellTask-->PostProcessingTask(s)
or
SetupTask(s)-->SupervisedShellTask-->PostProcessingTask(s)

raises_runtime_error is to catch a specific error from raising but since I 
choose to raise all errors in my setup, there's no need for this flag in the
ErrorHandler class. For the same reason, raise_on_max is also removed.

max_corrections is written in custodian such the ErrorHandler can never be
ran in parallel. I should switch where the correction count is stored. Perhaps
pass it in as an argument to the correct() method. This means I would have to
store the data at a higher level (in the SupervisedJobTask).
However, I don't see any example of this ever being used by Custodian so I 
just leave this out for the time being.
