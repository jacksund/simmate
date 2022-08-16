# -*- coding: utf-8 -*-

import pytest
from pandas import DataFrame

from simmate.database.base_data_types import StaticEnergy
from simmate.toolkit import Structure


@pytest.mark.django_db
def test_static_energy_table(structure, tmp_path):

    # test writing columns
    StaticEnergy.show_columns()

    # test writing to database
    structure_db = StaticEnergy.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
        structure=structure,
    )
    structure_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    structure_db2 = StaticEnergy.from_run_context(
        run_id="example-id-123",
        workflow_name="example.test.workflow",
    )
    assert structure_db.id == structure_db2.id

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new

    # test converting search results to dataframe and to toolkit
    df = StaticEnergy.objects.to_dataframe()
    assert isinstance(df, DataFrame)
    structures = StaticEnergy.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)

    # update the database entry using a Vasprun result.
    # from pymatgen.io.vasp.outputs import Vasprun
    # TODO:

    # test writing and reloading these from and archive
    archive_filename = tmp_path / "archive.zip"
    StaticEnergy.objects.to_archive(archive_filename)
    StaticEnergy.load_archive(
        archive_filename,
        confirm_override=True,
        delete_on_completion=True,
    )
