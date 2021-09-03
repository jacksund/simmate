# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------


class Executor:
    def __init__(self):
        # setup Client
        # connect to Client
        pass

    def submit(self, func, args=[], kwargs={}):
        # submit the function with inputs
        # return a key (or future) that allows accessing the job info
        pass

    def check(self, future_or_key):
        # using the key, grab the job info from the client
        # return the status of the job
        # This should be one of three statuses: pending, done, error
        pass

    def get_result(self, future_or_key):
        # note that this should only be called if the job is done!
        # using the key, grab the job info from the client
        # return the result of the job
        pass


# -----------------------------------------------------------------------------

# This is a testing-only executor that runs commands locally, immediately, and in-place.
# This means the entire Search will wait each time this is called until the
# calculation completes. User should switch to the DaskExecutor!
# The main benefit of this Executor is that it will raise the error with full
# trackback when the func fails. Thus this is strictly useful for troubleshooting.


class LocalExecutor:
    def __init__(self):
        pass

    def submit(self, func, args=[], kwargs={}):
        return func(*args, **kwargs)

    def check(self, future):
        return "done"

    def get_result(self, future):
        return future


# -----------------------------------------------------------------------------

from dask.distributed import Client

# !!! For some reason, when I return future.key in self.submit(...), it deletes the key from the client.
# !!! Therefore, I store the entire Future, not just the key.
# Whenever I attempt to load from a crashed run, I can try to reaccess Futures from the client via...
# from dask.distributed import Future
# future = Future(key, self.client)


class DaskExecutor:
    def __init__(self, address):
        # connect to Client
        self.client = Client(address)

    def submit(self, func, args=[], kwargs={}):

        # submit the flow with inputs
        future = self.client.submit(func, *args, **kwargs)

        # return a key to access job submission info
        return future

    def check(self, future):

        # Now check the status of the future
        if future.status == "pending":
            return "pending"
        elif future.status == "finished":
            return "done"
        elif future.status == "error":
            # if you want the actualy traceback error, use future.result()
            return "error"

    def get_result(self, future):
        return future.result()


# -----------------------------------------------------------------------------

from fireworks import LaunchPad, Workflow, Firework
from fireworks.user_objects.firetasks.script_task import PyTask


class FireWorksExecutor:
    def __init__(self):
        # connect to the LaunchPad (the client)
        self.launchpad = LaunchPad.from_file("my_launchpad.yaml")

        #!!! OPTIONAL empty the database
        self.launchpad.reset("", require_password=False)

    def submit(self, func, args=[], kwargs={}):  
        #!!! flow is required to be a string here like 'myrepo.workflows.DummyFlow' !!!

        # we make a WorkFlow that is made of one FireWork with only one FireTask
        firetask = PyTask(
            func=func, args=args, kwargs=kwargs, stored_data_varname="result"
        )
        firework = Firework(firetask)
        workflow = Workflow([firework])

        # submit the flow with inputs
        self.launchpad.add_wf(workflow)

        # fireworks is weird where there isn't a workflow id
        return firework.fw_id

    def check(self, key):

        # grab the future object from the client
        firework = self.launchpad.get_fw_by_id(key)

        # Now check the status of the future
        if firework.state == "READY" or firework.state == "RUNNING":
            return "pending"
        elif firework.state == "COMPLETED":
            return "done"
        elif firework.state == "FIZZLED":
            # I still want to delete the workflow
            #!!! The directory was likely not cleared!
            # self.launchpad.delete_wf(key)
            return "error"

    def get_result(self, key):

        # grab the future object from the client
        firework = self.launchpad.get_fw_by_id(key)

        # get the final launch associated with the firework
        launch = firework.launches[-1]

        # grab the output data
        # note that I set 'result' via 'stored_data_varname' above
        result = launch.action.stored_data["result"]

        # if you want the runtime
        # launch.runtime_secs

        # delete the workflow data
        self.launchpad.delete_wf(key)

        # return the result
        return result  #!!! result is not always returned as the correct object!


#!!! This code is for testing...
# from pymatgen.core.composition import Composition
# c = Composition('Ca2N')
# e = FireWorks()
# future = e.submit('pymatdisc.test.pytask.test_fnc', args=[c])
# # and launch it locally
# from fireworks.core.rocket_launcher import rapidfire , launch_rocket
# launch_rocket(e.launchpad)
# if launched remotely, wait until its done
# status = None
# while status != 'done':
#     status = e.check(future)
# result = e.get_result(future)

# -----------------------------------------------------------------------------

# TO-DO... Prefect
# Tip when writing: PyTask in Fireworks --> FunctionTask in Prefect
# https://docs.prefect.io/api/latest/tasks/function.html#functiontask

# -----------------------------------------------------------------------------

# TO-DO... SLURMExecutor

# I will need to create tempdir for this like USPEX does...

# This is ran on a local SLURM queue only
# Just like with Fireworks, I need the func given as a string where the string is a 
# importable function. For example, func='myrepo.workflows.DummyFlow'.

# To run a single function from the command line...
# https://stackoverflow.com/questions/3987041/run-function-from-the-command-line

# Here is an example templatefile
"""
#!/usr/bin/env bash

#SBATCH -J pymatdisc_job
#SBATCH -p p1
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --mem=10GB
#SBATCH -t 3-00:00:00
#SBATCH --output=job.%j.out
#SBATCH -N 1

{execute_cmd}
"""

class SLURMExecutor:
    def __init__(self, templatefile):
        self.templatefile = templatefile

    def submit(self, func, args=[], kwargs={}):  
        
        # open the templatefile
        with open(self.templatefile, "r") as file:
            # grab the content as a string
            lines = file.read()
        
        #!!! I should change what I have below to make tmpdir and make things like
        #!!! execute_cmd.py file, submit file, and so forth.
        
        # change the {execute_cmd} to match the code we want
        # The command will look like...
            # python -c 'import func; func(*args, **kwargs)
            #!!! There will be a bug if you have an input that a string like "it's"
        cmd = "python -c '{func}; {func}(*{args}, **{kwargs})' > $SLURM_JOB_ID.txt"
        cmd = cmd.format(func=func, args=args,kwargs=kwargs)
        lines.format(execute_cmd=cmd)
        
        #!!! TO-DO -- the rest of the steps below
        
        # write to a tempfile
        
        # submit the file
        
        # save the job id
        # example slurm output: Submitted batch job 12345
        
        # delete the tempfile
        
        return

    def check(self, key):
        return

    def get_result(self, key):
        return

# -----------------------------------------------------------------------------