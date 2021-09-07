# -*- coding: utf-8 -*-

import os

# import time import sleep
from timeit import default_timer as time

from subprocess import Popen

from custodian.custodian import Custodian, Job, ErrorHandler

from simmate.workflow_engine.tasks.supervised_staged_shell_task import (
    SupervisedStagedShellTask as SSSTask,
)
from simmate.workflow_engine.tasks.error_handler import ErrorHandler as ErrorHandlerS

import pandas

# the number total trials to run
ntrials = 500

# ----------------------------------------------------------------------------

# This tests the base time it takes to run a subprocess command without any
# additional features. You can think of this as the absolute fastest we can
# run commands in python.

base_times = []
for x in range(ntrials):
    # start the timer
    start = time()
    # run dummy command and wait for it to finish
    popen = Popen("echo dummy", shell=True)
    popen.wait()
    # stop the timer
    stop = time()
    # add time to db
    base_times.append(stop - start)

# ----------------------------------------------------------------------------

# This tests Simmate without any error handlers. This is the smallest amount
# of penalty you can have on top of a subprocess if you don't want to use
# any of Simmate's additional features.

# I add an "S" at the end of each to separate from the Custodian handlers


class AlwaysPassesHandlerS(ErrorHandlerS):
    def check(self, dir):
        return None

    def correct(self, dir):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysPassesMonitorS(AlwaysPassesHandlerS):
    is_monitor = True


class AlwaysPassesSpecialMonitorS(AlwaysPassesMonitorS):
    is_terminating = False


task = SSSTask(
    command="echo dummy",
    errorhandlers=[
        AlwaysPassesHandlerS(),
        AlwaysPassesMonitorS(),
        AlwaysPassesSpecialMonitorS(),
    ],
    polling_timestep=0,
    monitor_freq=1,
)

simmate_times = []
for x in range(ntrials):
    # start the timer
    start = time()
    # run dummy command and wait for it to finish
    result = task.run()
    # stop the timer
    stop = time()
    # add time to db
    simmate_times.append(stop - start)

# ----------------------------------------------------------------------------


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
    os.remove("custodian.json")

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
