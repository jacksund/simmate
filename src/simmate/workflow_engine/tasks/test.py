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

from simmate.workflow_engine.tasks.shelltask import ShellTask
from simmate.workflow_engine.error_handler import ErrorHandler
from simmate.workflow_engine.tasks.supervised_staged_shell_task import (
    SupervisedStagedShellTask as SSSTask,
    NonZeroExitError,
    MaxCorrectionsError,
    StructureRequiredError,
)

# ----------------------------------------------------------------------------

# make some simple StagedShellTasks for us to test with


class DummyTask(SSSTask):
    command = "echo dummy"


# ----------------------------------------------------------------------------

# make some simple Handlers to run tests with


class AlwaysPassesHandler(ErrorHandler):
    def check(self, dir):
        return None

    def correct(self, dir):
        # this should never be entered since check() never returns an error
        raise Exception


class AlwaysFailsHandler(ErrorHandler):
    def check(self, dir):
        return "ExampleError"

    def correct(self, dir):
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
        command="NonexistantCommand 404",
    )


def test_supervisedstagedshelltask():

    # running a basic task
    task = DummyTask(monitor=False)
    task.run()

    # requires structure failure
    task.requires_structure = True
    pytest.raises(StructureRequiredError, task.run)

    # test success, handler, monitor, and special-monitor
    task = DummyTask(
        error_handlers=[
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ],
        polling_timestep=0,
        monitor_freq=2,
    )
    assert task.run() == (None, [])

    # test result-only return, write corrections file, compressed out, and tempdir
    with TemporaryDirectory() as tempdir:
        task = DummyTask(
            error_handlers=[
                AlwaysPassesHandler(),
                AlwaysPassesMonitor(),
                AlwaysPassesSpecialMonitor(),
            ],
            return_corrections=False,
            save_corrections_tofile=True,
            compress_output=True,
            polling_timestep=0,
            monitor_freq=2,
        )
        assert task.run(dir=tempdir) is None
        assert os.path.exists(tempdir)

    # test nonzeo returncode
    task = DummyTask(
        command="NonexistantCommand 404",
        error_handlers=[AlwaysPassesHandler()],
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(NonZeroExitError, task.run)

    # testing handler-triggered failures
    task = DummyTask(
        error_handlers=[AlwaysFailsHandler()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)

    # monitor failure
    task = DummyTask(
        error_handlers=[AlwaysFailsMonitor()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)

    # special-monitor failure
    task = DummyTask(
        error_handlers=[AlwaysFailsSpecialMonitor()],
        return_corrections=False,
        polling_timestep=0,
        monitor_freq=2,
    )
    pytest.raises(MaxCorrectionsError, task.run)


# For manual testing
# %time test_shelltask()
# %time test_supervisedstagedshelltask()

# Notes on testing WorkflowRunTask...
#
# import prefect
# from prefect import task, Flow, Parameter
# from simmate.workflow_engine.tasks.workflow_task import WorkflowTask
# @task
# def hello_task1():
#     logger = prefect.context.get("logger")
#     logger.info("Hello world 1!")
# with Flow("hello-flow") as flow1:
#     hello_task1()
# flowtask1 = WorkflowTask(flow1)
# @task
# def hello_task2():
#     logger = prefect.context.get("logger")
#     logger.info("Hello world 2!")
# with Flow("hello-flow") as flow2:
#     labels = Parameter("labels")
#     flowtask1(labels=labels)
#     hello_task2()
# flow2.run(labels=["TEST"])
