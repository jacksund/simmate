# -*- coding: utf-8 -*-

"""
This script tests task running and monitoring. The benchmark looks at a `task.run()`
which calls the command "echo dummy". We compare the following:
    - a direct call to subprocess without any monitoring
    - a task written with Simmate and 3 dummy error handlers
    - a task written with Custodian and 3 dummy error handlers

Note, Simmate is currently slower than Custodian, but this is entirely because
Simmate carefully kills child Popen processes -- which takes 0.02s per task. When
this step is removed from all non-mpiruns, we see Simmate overhead is
significantly faster than Custodian. But I don't remove this out of fear of introducing
a bug, which I detail in the execute method of the S3Task. This bug is actually
present in Custodian for commands that spawn multiple processes/threads.
"""

from pathlib import Path
from subprocess import Popen
from timeit import default_timer as time

import pandas

# the number total trials to run
ntrials = 1000


def run_trials(fxn, ntrials, kwargs={}):
    trial_times = []
    for x in range(ntrials):
        start = time()
        fxn(**kwargs)
        stop = time()
        trial_times.append(stop - start)
    return trial_times


# ----------------------------------------------------------------------------

# a direct call to subprocess without any monitoring


def run_popen():
    popen = Popen("echo dummy", shell=True)
    popen.wait()


base_times = run_trials(run_popen, ntrials)

# ----------------------------------------------------------------------------

# a task written with Simmate and 3 dummy error handlers

from simmate.engine import ErrorHandler, S3Task


class AlwaysPassesHandler(ErrorHandler):
    def check(self, dir):
        return None

    def correct(self, dir):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysPassesMonitor(AlwaysPassesHandler):
    is_monitor = True


class AlwaysPassesSpecialMonitor(AlwaysPassesMonitor):
    is_terminating = False


class DummyTask(S3Task):
    command = "echo dummy"
    error_handlers = [
        AlwaysPassesHandler(),
        AlwaysPassesMonitor(),
        AlwaysPassesSpecialMonitor(),
    ]


task = DummyTask(polling_timestep=0, monitor_freq=1, monitor=False)

simmate_times = run_trials(task.run, ntrials, kwargs={"directory": "."})

# ----------------------------------------------------------------------------

# a task written with Custodian and 3 dummy error handlers

from custodian.custodian import Custodian, ErrorHandler, Job


class AlwaysPassesHandler(ErrorHandler):
    def check(self):
        return None

    def correct(self):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysPassesMonitor(AlwaysPassesHandler):
    is_monitor = True


class AlwaysPassesSpecialMonitor(AlwaysPassesMonitor):
    is_terminating = False


class DummyJob(Job):
    def setup(self):
        pass

    def run(self):
        return Popen("echo dummy", shell=True)

    def postprocess(self):
        pass


# I can't use run_trials here...

custodian_times = []
for x in range(ntrials):
    # I need to reset this each time
    custodian = Custodian(
        [
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ],
        [DummyJob()],
        polling_time_step=0,
        monitor_freq=1,
    )
    # start the timer
    start = time()
    # run dummy command and wait for it to finish
    result = custodian.run()
    # stop the timer
    stop = time()
    # add time to db
    custodian_times.append(stop - start)
    # I need to remove the log file, otherwise it builds and affects speed
    Path("custodian.json").unlink()

# ----------------------------------------------------------------------------

# PLOT RESULTS

dataframe = pandas.DataFrame.from_dict(
    {"base": base_times, "simmate": simmate_times, "custodian": custodian_times}
)

# line plot
dataframe.plot(y=["base", "simmate", "custodian"])

# histograms
for label in ["base", "simmate", "custodian"]:
    dataframe.plot(y=label, kind="hist")

# ----------------------------------------------------------------------------
