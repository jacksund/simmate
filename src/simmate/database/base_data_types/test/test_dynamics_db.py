# -*- coding: utf-8 -*-

import pytest
from pandas import DataFrame

from simmate.database.base_data_types import DynamicsIonicStep, DynamicsRun
from simmate.toolkit import Structure

# from pymatgen.io.vasp.outputs import Vasprun


@pytest.mark.django_db
def test_static_energy_table(structure):

    # test writing columns
    DynamicsRun.show_columns()
    DynamicsIonicStep.show_columns()

    # test writing to database
    structure_db = DynamicsRun.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
        structure=structure,
    )
    structure_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    structure_db2 = DynamicsRun.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
    )
    assert structure_db.id == structure_db.id

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new

    # test converting search results to dataframe and to toolkit
    df = DynamicsRun.objects.to_dataframe()
    assert isinstance(df, DataFrame)
    structures = DynamicsRun.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)
