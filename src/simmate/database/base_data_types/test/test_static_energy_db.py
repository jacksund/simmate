# -*- coding: utf-8 -*-

import os

import pytest

from pandas import DataFrame

# from pymatgen.io.vasp.outputs import Vasprun

from simmate.toolkit import Structure
from simmate.website.test_app.models import TestStaticEnergy


@pytest.mark.django_db
def test_static_energy_table(structure, tmpdir):

    # test writing columns
    TestStaticEnergy.show_columns()

    # test writing to database
    structure_db = TestStaticEnergy.from_prefect_id(
        prefect_flow_run_id="example-id-123",
        structure=structure,
    )
    structure_db.save()

    # try grabbing the calculation again and make sure it loaded from the
    # database rather than creating a new entry
    structure_db2 = TestStaticEnergy.from_prefect_id(
        prefect_flow_run_id="example-id-123",
    )
    assert structure_db.id == structure_db2.id

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new

    # test converting search results to dataframe and to toolkit
    df = TestStaticEnergy.objects.to_dataframe()
    assert isinstance(df, DataFrame)
    structures = TestStaticEnergy.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)

    # update the database entry using a Vasprun result.
    # TODO:

    # test writing and reloading these from and archive
    archive_filename = os.path.join(tmpdir, "archive.zip")
    TestStaticEnergy.objects.to_archive(archive_filename)
    TestStaticEnergy.load_archive(
        archive_filename,
        confirm_override=True,
        delete_on_completion=True,
    )
