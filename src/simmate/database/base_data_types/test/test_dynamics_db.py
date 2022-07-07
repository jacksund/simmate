# -*- coding: utf-8 -*-

import pytest

from pandas import DataFrame

# from pymatgen.io.vasp.outputs import Vasprun

from simmate.toolkit import Structure
from simmate.website.test_app.models import TestDynamicsRun, TestIonicStep


@pytest.mark.django_db
def test_static_energy_table(structure):

    # test writing columns
    TestDynamicsRun.show_columns()
    TestIonicStep.show_columns()

    # test writing to database
    structure_db = TestDynamicsRun.from_prefect_id(
        prefect_flow_run_id="example-id-123",
        structure=structure,
    )
    structure_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    structure_db2 = TestDynamicsRun.from_prefect_id(
        prefect_flow_run_id="example-id-123",
    )
    assert structure_db.id == structure_db.id

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new

    # test converting search results to dataframe and to toolkit
    df = TestDynamicsRun.objects.to_dataframe()
    assert isinstance(df, DataFrame)
    structures = TestDynamicsRun.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)
