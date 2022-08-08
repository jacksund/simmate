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
import shutil

import pytest

from prefect import flow

from simmate.workflow_engine import ErrorHandler, S3Workflow
from simmate.workflow_engine.s3_workflow import (
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
    class Customized__Testing__DummyWorkflow(S3Workflow):
        command = "echo dummy"
        use_database = False

    # for shorthand reference below
    workflow = Customized__Testing__DummyWorkflow

    assert isinstance(workflow.get_config(), dict)

    workflow.show_config()  # a print statment w. nothing else to check

    workflow._to_prefect_flow()  # unused for now

    # Test basic run
    state = workflow.run()
    result = state.result()
    assert state.is_completed()
    assert os.path.exists(result["directory"])
    shutil.rmtree(result["directory"])

    # Test as a subflow
    @flow
    def test():
        state = workflow.run()
        return state.result()

    state = test(return_state=True)
    result = state.result()

    assert state.is_completed()
    assert os.path.exists(result["directory"])
    shutil.rmtree(result["directory"])


def test_s3task_1():
    # run a basic task w.o. any handlers or monitoring

    class Customized__Testing__DummyWorkflow(S3Workflow):
        command = "echo dummy"
        use_database = False
        monitor = False

    output = Customized__Testing__DummyWorkflow.run_config()

    assert output["result"] == None
    assert output["corrections"] == []

    # make sure that a "simmate-task-*" directory was created
    assert os.path.exists(output["directory"])

    # and delete that directory
    os.rmdir(output["directory"])


def test_s3task_2():
    # test file compression

    class Customized__Testing__DummyWorkflow(S3Workflow):
        command = "echo dummy"
        use_database = False
        monitor = False

    output = Customized__Testing__DummyWorkflow.run_config(compress_output=True)

    # make sure that a "simmate-task-*.zip" archive was created
    assert os.path.exists(output["directory"] + ".zip")

    # make sure that a "simmate-task-*" directory was removed
    assert not os.path.exists(output["directory"])

    # and delete the archive
    os.remove(output["directory"] + ".zip")


def test_s3task_3(tmpdir):
    # Make a task with error handlers, monitoring, and specific directory

    class Customized__Testing__DummyWorkflow(S3Workflow):
        command = "echo dummy"
        use_database = False
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [
            AlwaysPassesHandler(),
            AlwaysPassesMonitor(),
            AlwaysPassesSpecialMonitor(),
        ]

    # use the temporary directory
    assert Customized__Testing__DummyWorkflow.run_config(directory=tmpdir) == {
        "result": None,
        "corrections": [],
        "directory": tmpdir,
    }


def test_s3task_4(tmpdir):
    # test nonzero returncode

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "NonexistantCommand 404"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysPassesHandler()]

    pytest.raises(
        NonZeroExitError,
        Customized__Testing__DummyWorkflow.run_config,
        directory=tmpdir,
    )


def test_s3task_5(tmpdir):
    # testing handler-triggered failures

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsHandler()]

    pytest.raises(
        MaxCorrectionsError,
        Customized__Testing__DummyWorkflow.run_config,
        directory=tmpdir,
    )


def test_s3task_6(tmpdir):
    # monitor failure

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsMonitor()]

    pytest.raises(
        MaxCorrectionsError,
        Customized__Testing__DummyWorkflow.run_config,
        directory=tmpdir,
    )


def test_s3task_7(tmpdir):
    # special-monitor failure (non-terminating monitor)

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsSpecialMonitorRetry()]

    pytest.raises(
        MaxCorrectionsError,
        Customized__Testing__DummyWorkflow.run_config,
        directory=tmpdir,
    )


def test_s3task_8(tmpdir):
    # check that monitor exits cleanly when retries are not allowed and no
    # workup method raises an error

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "echo dummy"
        polling_timestep = 0
        monitor_freq = 2
        error_handlers = [AlwaysFailsSpecialMonitorNoRetry()]

    result = Customized__Testing__DummyWorkflow.run_config(directory=tmpdir)
    assert len(result["corrections"]) == 1


def test_s3task_9(tmpdir):
    # make sure an error is raised when a file is missing

    class Customized__Testing__DummyWorkflow(S3Workflow):
        use_database = False
        command = "echo dummy"
        required_files = ["FILE_THAT_DOESNT_EXIST"]

    pytest.raises(
        Exception,
        Customized__Testing__DummyWorkflow.run_config,
        directory=tmpdir,
    )
