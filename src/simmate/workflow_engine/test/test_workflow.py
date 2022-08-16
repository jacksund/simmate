# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import TestCalculation
from simmate.workflow_engine import Workflow


class DummyProject__DummyCaclulator__DummyPreset(Workflow):
    """
    Minimal example of a workflow
    """

    use_database = False

    # TODO: test database registration and results
    database_table = TestCalculation
    # @classmethod
    # def _save_to_database(cls, result):
    #     pass  # Skip default which is meant for vasp calcs

    @staticmethod
    def run_config(source=None, structure=None, **kwargs):
        return 1 + 2


# copy to variable for shorthand use
DummyFlow = DummyProject__DummyCaclulator__DummyPreset


@pytest.mark.django_db
def test_workflow(tmp_path):

    # Same exact thing but using higher-level method
    state = DummyFlow.run(directory=tmp_path)
    assert state.is_completed()
    assert state.result() == 3

    # testing naming conventions
    assert DummyFlow.name_full == "dummy-project.dummy-caclulator.dummy-preset"
    assert DummyFlow.name_type == "dummy-project"
    assert DummyFlow.name_calculator == "dummy-caclulator"
    assert DummyFlow.name_preset == "dummy-preset"

    # testing class properties
    assert DummyFlow.description_doc == DummyFlow.__doc__
    assert DummyFlow.description_doc.strip() == "Minimal example of a workflow"
    assert DummyFlow.parameter_names == [
        "compress_output",
        "directory",
        "run_id",
        "source",
        "structure",
    ]
    assert DummyFlow._parameters_to_register == [
        "directory",
        "run_id",
        "source",
    ]
    DummyFlow.show_parameters()  # a print statment w. nothing else to check

    assert isinstance(DummyFlow.get_config(), dict)

    DummyFlow.show_config()  # a print statment w. nothing else to check

    # test file compression
    new_dir = tmp_path / "new_folder"
    state = DummyFlow.run(directory=new_dir, compress_output=True)
    result = state.result()

    # make sure that a "simmate-task-*.zip" archive was created
    assert new_dir.with_suffix(".zip").exists()

    # make sure that a "simmate-task-*" directory was removed
    assert not new_dir.exists()

    # and delete the archive
    new_dir.with_suffix(".zip").unlink()


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


# !!! These tests below are for the Prefect Executor, which is disabled at the moment

# @task
# def dummy_task_1(a):
#     return 1
# @task
# def dummy_task_2(a):
#     return 2
# @staticmethod
# def run_config(source=None, structure=None, **kwargs):
#     x = dummy_task_1(source)
#     y = dummy_task_2(structure)
#     return x + y

# # Run the workflow just like you would for the base Prefect class
# flow = DummyFlow._to_prefect_flow()
# state = flow(return_state=True, directory=tmp_path)
# assert state.is_completed()
# assert state.result() == 3

# @pytest.mark.prefect_db
# @pytest.mark.django_db
# def test_workflow_cloud(mocker, sample_structures):
#     # test cloud properties
#     deployment_id = DummyFlow.deployment_id
#     assert isinstance(deployment_id, str)
#     # we dont check the actual value bc its randomly generated
#     n = DummyFlow.nflows_submitted
#     assert isinstance(n, int)
#     # to test serialization of input parameters we grab a toolkit object
#     structure = sample_structures["C_mp-48_primitive"]
#     # Run the workflow through prefect cloud
#     flow_id = DummyFlow.run_cloud(structure=structure)
#     assert isinstance(flow_id, str)
