# -*- coding: utf-8 -*-

import pytest

from simmate.workflow_engine import Workflow, task


@task
def dummy_task_1(a):
    return 1


@task
def dummy_task_2(a):
    return 2


class Dummy_Project__Dummy_Caclulator__Dummy_Preset(Workflow):
    """
    Minimal example of a workflow
    """

    # database_table = TestStructureCalculation
    register_kwargs = ["source", "structure"]

    @staticmethod
    def run(source=None, structure=None, **kwargs):
        x = dummy_task_1(source)
        y = dummy_task_2(structure)
        return x.result() + y.result()


# copy to variable for shorthand use
DummyFlow = Dummy_Project__Dummy_Caclulator__Dummy_Preset


def test_workflow():
    # Run the workflow just like you would for the base Prefect class
    flow = DummyFlow.to_prefect_flow()
    state = flow()
    assert state.is_completed()
    assert state.result() == 3

    # Same exact thing but using higher-level method
    state = DummyFlow.run_as_prefect_flow()
    assert state.is_completed()
    assert state.result() == 3

    # testing naming conventions
    assert DummyFlow.name_full == "dummy-project.dummy-caclulator.dummy-preset"
    assert DummyFlow.name_project == "dummy-project"
    assert DummyFlow.name_calculator == "dummy-caclulator"
    assert DummyFlow.name_preset == "dummy-preset"

    # testing class properties
    assert DummyFlow.description_doc == DummyFlow.__doc__
    assert DummyFlow.description_doc.strip() == "Minimal example of a workflow"
    assert DummyFlow.parameter_names == ["kwargs", "source", "structure"]
    DummyFlow.show_parameters()  # a print statment w. nothing else to check


@pytest.mark.django_db
def test_workflow_cloud(mocker, sample_structures):

    # from simmate.workflow_engine.common_tasks import load_input_and_register
    # from simmate.website.test_app.models import TestStructureCalculation

    # from prefect.client import Client
    # from prefect.backend import flow_run

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
    mocker.patch.object(
        load_input_and_register, "run", return_value={"structure": structure}
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
    Workflow._serialize_parameters(**parameters)


def test_deserialize_parameters(mocker):

    # -------
    # We don't want to actually call these methods, but just ensure that they
    # have been called.
    from simmate.toolkit import Structure
    from simmate.toolkit.diffusion import MigrationHop

    mocker.patch.object(
        Structure,
        "from_dynamic",
    )
    mocker.patch.object(
        MigrationHop,
        "from_dynamic",
    )
    # -------

    example_parameters = {
        "migration_hop": None,
        "supercell_start": None,
        "supercell_end": None,
        "structures": "None; None; None",
    }

    Workflow._deserialize_parameters(**example_parameters)
