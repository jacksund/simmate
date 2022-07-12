# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files
from simmate.workflow_engine import S3Task
from simmate.calculators.vasp.inputs import Potcar
from simmate.calculators.vasp.workflows.diffusion.all import (
    Diffusion__Vasp__NebAllPaths,
)


@pytest.mark.django_db
@pytest.mark.prefect_bug
def test_neb(sample_structures, tmpdir, mocker):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="all_paths",
    )

    # For testing, look at I- diffusion in Y2CF2
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(Potcar, "to_file_from_type", return_value=None)

    # We also don't want to run any commands -- for any task. We skip these
    # by having the base S3task.execute just return an empty list (meaning
    # no corrections were made).
    mocker.patch.object(S3Task, "execute", return_value=[])

    # Don't check for proper input files because POTCARs will be missing
    mocker.patch.object(S3Task, "_check_input_files", return_value=None)

    # run the workflow and make sure it handles data properly.
    state = Diffusion__Vasp__NebAllPaths.run(
        structure=structure,
        migrating_specie="I",
        command="dummycmd1; dummycmd2; dummycmd3",
        directory=str(tmpdir),
    )
    assert state.is_completed()

    # BUG: If this job hangs, this line can break that can have it exit
    # the pytest command successfully. Still trying to figure out why.
    Diffusion__Vasp__NebAllPaths.nflows_submitted
    #
    # As a minimal example, I can get a test to hang in a lone test using...
    #
    # from prefect import flow, task
    # from simmate.database import connect  # causes the hanging test
    # @task
    # def dummy_task_1(a):
    #     return 1
    # @task
    # def dummy_task_2(a):
    #     return 2
    # @flow
    # def run_config(source=None, structure=None, **kwargs):
    #     x = dummy_task_1(source)
    #     y = dummy_task_2(structure)
    #     return x.result() + y.result()
    # def test_workflow():
    #     state = run_config()
    #     assert state.is_completed()
    #     assert state.result() == 3
