# -*- coding: utf-8 -*-

import pytest

from simmate.workflow_engine import Workflow, task
from simmate.website.test_app.models import TestStructureCalculation


@task
def dummy_task_1(a):
    return 1


@task
def dummy_task_2(a):
    return 2


class DummyProject__DummyCaclulator__DummyPreset(Workflow):
    """
    Minimal example of a workflow
    """

    database_table = TestStructureCalculation

    @staticmethod
    def run_config(source=None, structure=None, **kwargs):
        x = dummy_task_1(source)
        y = dummy_task_2(structure)
        return x.result() + y.result()


# copy to variable for shorthand use
DummyFlow = DummyProject__DummyCaclulator__DummyPreset


@pytest.mark.prefect_bug
def test_workflow():
    # Run the workflow just like you would for the base Prefect class
    flow = DummyFlow.to_prefect_flow()
    state = flow()
    assert state.is_completed()
    assert state.result() == 3

    # Same exact thing but using higher-level method
    state = DummyFlow.run()
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
    assert DummyFlow.parameters_to_register == [
        "prefect_flow_run_id",
        "source",
        "structure",
    ]
    DummyFlow.show_parameters()  # a print statment w. nothing else to check

    # test cloud properties

    # deployment_id = DummyFlow.deployment_id
    # assert isinstance(deployment_id, str)
    # we dont check the actual value bc its randomly generated

    n = DummyFlow.nflows_submitted
    assert isinstance(n, int)
    # we dont check the actual value bc it could be affected by other parallel tests
    # BUG: see https://github.com/jacksund/simmate/issues/187


@pytest.mark.prefect_bug  # occassionally fails due to connect timeout
@pytest.mark.django_db
def test_workflow_cloud(mocker, sample_structures):

    # to test serialization of input parameters we grab a toolkit object
    structure = sample_structures["C_mp-48_primitive"]

    # Run the workflow through prefect cloud
    flow_id = DummyFlow.run_cloud(structure=structure)
    assert isinstance(flow_id, str)


def test_serialize_parameters():
    class TestParameter1:
        def to_dict(self):
            return {}

    class TestParameter2:
        """requires cloudpickle to serialize"""

        a = 123

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
