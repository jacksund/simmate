# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import (
    table_column,
    TestDatabaseTable,
    TestDatabaseTable2,
)


@pytest.mark.django_db
def test_database_table():

    # add a row
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()


@pytest.mark.django_db
def test_create_subclass():
    # same as before but this table was made by the create_subclass method
    x = TestDatabaseTable2(column1=True, column2=3.14, new_column3=False)
    x.save()


@pytest.mark.django_db
def test_show_columns():
    TestDatabaseTable.show_columns()


@pytest.mark.django_db
def test_to_dataframe():
    TestDatabaseTable.objects.to_dataframe()


@pytest.mark.django_db
def test_to_toolkit():
    with pytest.raises(Exception):
        TestDatabaseTable.objects.to_toolkit()


@pytest.mark.django_db
def test_from_toolkit():

    # to object and save
    x = TestDatabaseTable.from_toolkit(column1=True, column2=3.14)
    x.save()

    # to a dictionary
    y = TestDatabaseTable.from_toolkit(column1=True, column2=3.14, as_dict=True)
    assert isinstance(y, dict)


@pytest.mark.django_db
def test_archive():

    # add a row
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()

    # write to a file
    TestDatabaseTable.objects.to_archive()

    # try reloading
    with pytest.raises(Exception):
        TestDatabaseTable.load_archive()

    # try again with confirmation. This is also our last test so we can
    # delete the archive when we're done
    TestDatabaseTable.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )
