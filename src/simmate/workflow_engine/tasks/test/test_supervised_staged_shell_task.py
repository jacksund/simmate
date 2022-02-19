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

import pytest

from simmate.workflow_engine.error_handler import ErrorHandler
from simmate.workflow_engine.tasks.supervised_staged_shell_task import (
    S3Task,
    NonZeroExitError,
    MaxCorrectionsError,
    StructureRequiredError,
)

# ----------------------------------------------------------------------------

# make some a simple S3Task and ErrorHandlers for us to test with


class DummyTask(S3Task):
    command = "echo dummy"


class AlwaysPassesHandler(ErrorHandler):
    def check(self, directory):
        return None

    def correct(self, directory):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysFailsHandler(ErrorHandler):
    def check(self, directory):
        return True

    def correct(self, directory):
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


def test_s3task_1():
    # run a basic task
    task = DummyTask(monitor=False)
    output = task.run()

    # make sure that a "simmate-task-*" directory was created
    assert os.path.exists(output["directory"])

    # and delete that directory
    os.rmdir(output["directory"])


def test_s3task_2():
    # run a basic task
    task = DummyTask(monitor=False, compress_output=True)
    output = task.run()

    # make sure that a "simmate-task-*.zip" archive was created
    assert os.path.exists(output["directory"] + ".zip")

    # make sure that a "simmate-task-*" directory was removed
    assert not os.path.exists(output["directory"])

    # and delete the archive
    os.remove(output["directory"] + ".zip")


def test_s3task_3():
    # Make sure an error is raised when the task requires a structure but isn't
    # given one
    task = DummyTask(monitor=False)
    task.requires_structure = True
    pytest.raises(StructureRequiredError, task.run)


def test_s3task_4(tmpdir):
    # Make a task with error handlers and monitoring
    task = DummyTask(
        polling_timestep=0,
        monitor_freq=2,
    )
    task.error_handlers = [
        AlwaysPassesHandler(),
        AlwaysPassesMonitor(),
        AlwaysPassesSpecialMonitor(),
    ]
    # use the temporary directory
    assert task.run(directory=tmpdir) == {
        "result": None,
        "corrections": [],
        "directory": tmpdir,
        "prefect_flow_run_id": None,
    }


def test_s3task_5(tmpdir):
    # test nonzero returncode
    task = DummyTask(
        polling_timestep=0,
        monitor_freq=2,
    )
    task.command = "NonexistantCommand 404"
    task.error_handlers = [AlwaysPassesHandler()]
    pytest.raises(NonZeroExitError, task.run, directory=tmpdir)


def test_s3task_6(tmpdir):
    # testing handler-triggered failures
    task = DummyTask(
        polling_timestep=0,
        monitor_freq=2,
    )
    task.error_handlers = [AlwaysFailsHandler()]
    pytest.raises(MaxCorrectionsError, task.run, directory=tmpdir)


def test_s3task_7(tmpdir):
    # monitor failure
    task = DummyTask(
        polling_timestep=0,
        monitor_freq=2,
    )
    task.error_handlers = [AlwaysFailsMonitor()]
    pytest.raises(MaxCorrectionsError, task.run, directory=tmpdir)


def test_s3task_8(tmpdir):
    # special-monitor failure (non-terminating monitor)
    task = DummyTask(
        polling_timestep=0,
        monitor_freq=2,
    )
    task.error_handlers = [AlwaysFailsSpecialMonitor()]
    pytest.raises(MaxCorrectionsError, task.run, directory=tmpdir)
