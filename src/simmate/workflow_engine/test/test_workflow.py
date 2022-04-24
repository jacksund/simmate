# -*- coding: utf-8 -*-

import pytest

from prefect import Client
from prefect.backend import flow_run

from simmate.workflow_engine.workflow import Workflow, task, Parameter
from simmate.website.test_app.models import TestStructureCalculation


@task
def dummy_task_1(a):
    return 1


@task
def dummy_task_2(a):
    return 2


with Workflow("dummy-flowtype/dummy-flow") as DUMMY_FLOW:
    source = Parameter("source", default=None)
    structure = Parameter("structure", default=None)
    dummy_task_1(source)
    dummy_task_2(structure)
DUMMY_FLOW.calculation_table = TestStructureCalculation
DUMMY_FLOW.register_kwargs = ["prefect_flow_run_id", "source", "structure"]


def test_workflow():
    # Run the workflow just like you would for the base Prefect class
    DUMMY_FLOW.run()

    # testing naming conventions
    assert DUMMY_FLOW.type == "dummy-flowtype"
    assert DUMMY_FLOW.name_short == "dummy-flow"
    assert DUMMY_FLOW.description_doc == DUMMY_FLOW.__doc__


@pytest.mark.django_db
def test_workflow_cloud(mocker, sample_structures):

    # to test serialization of input parameters we grab a toolkit object
    structure = sample_structures["C_mp-48_primitive"]

    # -----------------
    # Because we won't have Prefect Cloud configured, we need to override some
    # methods so this test runs properly

    class DummyFlowView:
        flow_id = "example-flow-id-12345"

    class DummyFlowRunView:
        name = "example name"
        id = "example-flow-id-12345"

        def get_latest(self):
            pass

    class DummyMessage:
        level = 0
        message = "example message"

    mocker.patch.object(
        flow_run.FlowView,
        "from_flow_name",
        return_value=DummyFlowView(),
    )
    mocker.patch.object(
        Client,
        "create_flow_run",
        return_value="example-flowrun-id-12345",
    )
    mocker.patch.object(
        flow_run.FlowRunView,
        "from_flow_run_id",
        return_value=DummyFlowRunView(),
    )
    mocker.patch.object(
        Client,
        "get_cloud_url",
        return_value="example-url.com",
    )
    # BUG: I'm unable to patch this method and I can't figure out why...
    mocker.patch.object(
        flow_run,
        "watch_flow_run",
        return_value=[DummyMessage(), DummyMessage(), DummyMessage()],
    )
    # -----------------

    # Run the workflow through prefect cloud
    DUMMY_FLOW.run_cloud(wait_for_run=False, structure=structure)
    DUMMY_FLOW.run_cloud(wait_for_run=True, structure=structure)


def test_workflows_submitted(mocker):
    mocker.patch.object(
        Client,
        "graphql",
        return_value={"data": {"flow_run_aggregate": {"aggregate": {"count": 4}}}},
    )
    assert DUMMY_FLOW.nflows_submitted == 4


def test_serialize_parameters():
    class TestParameter1:
        def to_dict(self):
            return {}

    class TestParameter2:
        a = "can't serialize"

    parameters = dict(
        a=TestParameter1(),
        b=TestParameter2(),
    )
    Workflow._serialize_parameters(parameters)


def test_parameter_names():

    assert DUMMY_FLOW.parameter_names == ["source", "structure"]

    # simply prints out content so there's nothing to check here
    DUMMY_FLOW.show_parameters()
