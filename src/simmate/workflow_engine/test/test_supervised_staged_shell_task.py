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

from prefect import flow

from simmate.workflow_engine import ErrorHandler, S3Task
from simmate.workflow_engine.supervised_staged_shell_task import (
    NonZeroExitError,
    MaxCorrectionsError,
)

# ----------------------------------------------------------------------------

# make some a simple ErrorHandlers for us to test with


class AlwaysPassesHandler(ErrorHandler):
    def check(self, directory):
        return False

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
    has_custom_termination = True

    def terminate_job(self, directory, **kwargs):
        return True


class AlwaysFailsSpecialMonitorRetry(AlwaysFailsMonitor):
    has_custom_termination = True

    def terminate_job(self, directory, **kwargs):
        return True


class AlwaysFailsSpecialMonitorNoRetry(AlwaysFailsMonitor):
    has_custom_termination = True

    def terminate_job(self, directory, **kwargs):
        return False


# ----------------------------------------------------------------------------


@pytest.mark.prefect_db
def test_s3task_methods():
    class DummyTask(S3Task):
        command = "echo dummy"

    assert isinstance(DummyTask.get_config(), dict)

    DummyTask.print_config()  # a print statment w. nothing else to check

    DummyTask.to_prefect_task()  # unused for now

    @flow
    def test():
        task = DummyTask.run()
        return task.result()

    state = test(return_state=True)
    result = state.result()

    assert state.is_completed()
    assert os.path.exists(result["directory"])
    os.rmdir(result["directory"])


def test_s3task_1():
    # run a basic task w.o. any handlers or monitoring

    class DummyTask(S3Task):
        command = "echo dummy"
        monitor = False

    output = DummyTask.run_config()

    assert output["result"] == None
    assert output["corrections"] == []
    assert output["prefect_flow_run_id"] == None

    # make sure that a "simmate-task-*" directory was created
    assert os.path.exists(output["directory"])

    # and delete that directory
    os.rmdir(output["directory"])


def test_s3task_2():
    # test file compression

    class DummyTask(S3Task):
        command = "echo dummy"
        monitor = False
        compress_output = True

    output = DummyTask.run_config()

    # make sure that a "simmate-task-*.zip" archive was created
    assert os.path.exists(output["directory"] + ".zip")

    # make sure that a "simmate-task-*" directory was removed
    assert not os.path.exists(output["directory"])

    # and delete the archive
    os.remove(output["directory"] + ".zip")


def test_s3task_3(tmpdir):
    # Make a task with error handlers, monitoring, and specific directory

    class DummyTask(S3Task):
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ]

    # use the temporary directory
    assert DummyTask.run_config(directory=tmpdir) == {
        "result": None,
        "corrections": [],
        "directory": tmpdir,
        "prefect_flow_run_id": None,
    }


def test_s3task_4(tmpdir):
    # test nonzero returncode

    class DummyTask(S3Task):
        command = "NonexistantCommand 404"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysPassesHandler()]

    pytest.raises(
        NonZeroExitError,
        DummyTask.run_config,
        directory=tmpdir,
    )


def test_s3task_5(tmpdir):
    # testing handler-triggered failures

    class DummyTask(S3Task):
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsHandler()]

    pytest.raises(
        MaxCorrectionsError,
        DummyTask.run_config,
        directory=tmpdir,
    )


def test_s3task_6(tmpdir):
    # monitor failure

    class DummyTask(S3Task):
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsMonitor()]

    pytest.raises(
        MaxCorrectionsError,
        DummyTask.run_config,
        directory=tmpdir,
    )


def test_s3task_7(tmpdir):
    # special-monitor failure (non-terminating monitor)

    class DummyTask(S3Task):
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsSpecialMonitorRetry()]

    pytest.raises(
        MaxCorrectionsError,
        DummyTask.run_config,
        directory=tmpdir,
    )


def test_s3task_8(tmpdir):
    # check that monitor exits cleanly when retries are not allowed and no
    # workup method raises an error

    class DummyTask(S3Task):
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsSpecialMonitorRetry()]

    result = DummyTask.run_config(directory=tmpdir)
    assert len(result["corrections"]) == 1


def test_s3task_8(tmpdir):
    # make sure an error is raised when a file is missing

    class DummyTask(S3Task):
        command = "echo dummy"
        required_files = ["FILE_THAT_DOESNT_EXIST"]

    pytest.raises(
        Exception,
        DummyTask.run_config,
        directory=tmpdir,
    )
