# -*- coding: utf-8 -*-

import pytest

from pandas import DataFrame

from simmate.toolkit import Structure
from simmate.website.test_app.models import TestStructure


@pytest.mark.django_db
def test_structure_table(structure):

    # test writing columns
    TestStructure.show_columns()

    # test writing to database
    structure_db = TestStructure.from_toolkit(structure=structure)
    structure_db.save()

    # test writing to dictionary
    structure_dict = TestStructure.from_toolkit(structure=structure, as_dict=True)
    assert isinstance(structure_dict, dict)

    # test converting back to toolkit and ensuring the structure is the
    # same as before
    structure_new = structure_db.to_toolkit()
    assert structure == structure_new


@pytest.mark.django_db
def test_structure_queries():

    # test converting search results to dataframe and to toolkit
    df = TestStructure.objects.to_dataframe()
    assert isinstance(df, DataFrame)

    structures = TestStructure.objects.to_toolkit()
    assert isinstance(structures, list)
    assert isinstance(structures[0], Structure)


@pytest.mark.django_db
def test_structure_archives():

    TestStructure.objects.to_archive()
    TestStructure.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )
