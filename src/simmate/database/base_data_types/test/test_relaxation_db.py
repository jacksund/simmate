# -*- coding: utf-8 -*-

import pytest
from pandas import DataFrame

from simmate.database.base_data_types import IonicStep, Relaxation
from simmate.toolkit import Structure

# from pymatgen.io.vasp.outputs import Vasprun


@pytest.mark.django_db
def test_relaxation_table(structure):

    # test writing columns
    Relaxation.show_columns()
    IonicStep.show_columns()

    # test writing to database
    structure_db = Relaxation.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
        structure=structure,
    )
    structure_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    structure_db2 = Relaxation.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
    )
    assert structure_db.id == structure_db2.id

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new

    # test converting search results to dataframe and to toolkit
    df = Relaxation.objects.to_dataframe()
    assert isinstance(df, DataFrame)
    structures = Relaxation.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)
