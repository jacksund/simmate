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

import os
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

import pytest

from simmate.workflows.core.tasks.shelltask import ShellTask
from simmate.workflows.core.tasks.errorhandler import ErrorHandler
from simmate.workflows.core.tasks.stagedshelltask import StagedShellTask
from simmate.workflows.core.tasks.supervisedstagedtask import (
    SupervisedStagedTask,
    NonZeroExitError,
    MaxCorrectionsError,
)

# ----------------------------------------------------------------------------

# make some simple StagedShellTasks for us to test with


class DummyTask(StagedShellTask):
    command = "echo dummy"


class DummyAddFileTask(StagedShellTask):
    command = "echo dummy > DummyFileTask.out"

# ----------------------------------------------------------------------------

# make some simple Handlers to run tests with


class AlwaysPassesHandler(ErrorHandler):
    def check(self, dir):
        return None

    def correct(self, error, dir):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysFailsHandler(ErrorHandler):
    def check(self, dir):
        return "ExampleError"

    def correct(self, error, dir):
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


def test_shelltask():
    task = ShellTask()
    task.run(command="echo dummy")
    # TODO - I should silence prefect logging at a higher level for all tests
    pytest.raises(
        CalledProcessError,
        task.run,
        command='NonexistantCommand 404',)


def test_stagedshelltask():

    # test individual methods
    task = DummyTask()
    task.setup()
    task.execute()
    task.postprocess()
    task.run()

    # test overwriting a kwarg
    task.run(command='echo dummyoverride')


def test_supervisedstagedtask():

    # test success, handler, monitor, and special-monitor
    task = SupervisedStagedTask(
        stagedtask=DummyTask(),
        errorhandlers=[
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ],
        polling_timestep=0,
        monitor_freq=2,
    )
    assert task.run() == (None, [])

    # test result-only return, compressed out, and tempdir
    with TemporaryDirectory() as tempdir:
        task = SupervisedStagedTask(
            stagedtask=DummyTask(),
            errorhandlers=[
                AlwaysPassesHandler(),
                AlwaysPassesMonitor(),
                AlwaysPassesSpecialMonitor(),
                ],
            return_corrections=False,
            compress_output=True,
            polling_timestep=0,
            monitor_freq=2,
        )
        assert task.run(dir=tempdir) is None
        assert os.path.exists(tempdir)

    # test nonzeo returncode
    task = SupervisedStagedTask(
        stagedtask=DummyTask(command='NonexistantCommand 404'),
        errorhandlers=[AlwaysPassesHandler()],
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(NonZeroExitError, task.run)

    # testing handler-triggered failures
    task = SupervisedStagedTask(
        stagedtask=DummyTask(),
        errorhandlers=[AlwaysFailsHandler()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)

    task = SupervisedStagedTask(
        stagedtask=DummyTask(),
        errorhandlers=[AlwaysFailsMonitor()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)

    task = SupervisedStagedTask(
        stagedtask=DummyTask(),
        errorhandlers=[AlwaysFailsSpecialMonitor()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)

# For manual testing
# %time test_shelltask()
# %time test_stagedshelltask()
# %time test_supervisedstagedtask()
