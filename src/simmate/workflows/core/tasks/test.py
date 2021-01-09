# -*- coding: utf-8 -*-

# Example job(s) [with and without subprocess.Popen]
# Example handler(s)

# Test...
# setup a working directory when given None, tempdir, and string of dir
# non-zero exit code raises error
# output compression (assert location and content)
# log output (assert naming, content, and location)
# return corrections (on and off)
# a simple SupervisedJobTask run (without handlers, with, and with monitors)
# run with and without handlers
# run with and without monitors
# terminate with a monitor
# terminate with a special-case monitor
# catch error with a non-monitor
# test max_errors limit

from subprocess import Popen

import pytest

from simmate.workflows.core.tasks.errorhandler import ErrorHandler
from simmate.workflows.core.tasks.job import Job
from simmate.workflows.core.tasks.supervisedjob import SupervisedJobTask

# ----------------------------------------------------------------------------

# make some dummy Jobs to run tests with


class DummyJob(Job):
    def setup(self):
        pass

    def execute(self):
        return "ExampleFuture"

    def postprocess(self):
        return "ExampleResult"


class PopenJob(DummyJob):
    def execute(self):
        return Popen("echo ExamplePopen", shell=True)


# ----------------------------------------------------------------------------

# make some dummy Handlers to run tests with


class AlwaysPassesHandler(ErrorHandler):
    def check(self):
        return None

    def correct(self):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysFailsHandler(ErrorHandler):
    def check(self):
        return "ExampleError"

    def correct(self):
        return "ExampleCorrection"


class AlwaysPassesMonitor(AlwaysPassesHandler):
    is_monitor = True


class AlwaysFailsMonitor(AlwaysFailsHandler):
    is_monitor = True


class AlwaysPassesSpecialMonitor(AlwaysPassesMonitor):
    is_terminating = False


class AlwaysFailsSpecialMonitor(AlwaysFailsMonitor):
    is_terminating = False


# ----------------------------------------------------------------------------

# !!! use itertools to make every combination of Handlers and Jobs?

def test_basic_supervision():

    # test success
    task = SupervisedJobTask(
        job=DummyJob(), errorhandlers=[AlwaysPassesHandler(), AlwaysPassesHandler()]
    )
    assert task.run() == ("ExampleResult", [])

    # test result-only return
    task = SupervisedJobTask(
        job=DummyJob(),
        errorhandlers=[AlwaysPassesHandler(), AlwaysPassesHandler()],
        return_corrections=False,
    )
    assert task.run() == "ExampleResult"

    # test max errors and failure
    task = SupervisedJobTask(
        job=DummyJob(),
        errorhandlers=[AlwaysFailsHandler()],
    )
    pytest.raises(Exception, task.run)

    # test popen success
    task = SupervisedJobTask(
        job=PopenJob(),
        errorhandlers=[AlwaysPassesHandler()],
    )
    assert task.run() == ("ExampleResult", [])

    # test popen monitors and special monitors
    task = SupervisedJobTask(
        job=PopenJob(),
        errorhandlers=[
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ],
        polling_timestep=0,
        monitor_freq=2,
    )
    assert task.run() == ("ExampleResult", [])

    # test popen monitors and special monitors
    task = SupervisedJobTask(
        job=PopenJob(),
        errorhandlers=[
            AlwaysPassesHandler(),
            AlwaysFailsMonitor(),
            AlwaysPassesSpecialMonitor(),
        ],
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(Exception, task.run)


%time test_basic_supervision()
