# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import (
    TestDatabaseTable,
    TestDatabaseTable2,
)


@pytest.mark.django_db
def test_database_table():

    # add a row
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()

    # check name
    assert x.get_table_name() == x.__class__.__name__


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

    # BUG: This test does not save archives within a tmpdir -- but instead the
    # working directory. Therefore, these tests cannot be split up and ran
    # in parallel (with pytest-xdist).

    # add sample rows
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()
    y = TestDatabaseTable(column1=False, column2=-3.14)
    y.save()

    # Also try to load an archive that doesn't exist yet
    with pytest.raises(FileNotFoundError):
        TestDatabaseTable.load_archive(
            confirm_override=True,
        )

    # write to a file
    TestDatabaseTable.objects.to_archive()

    # try reloading without confirming override
    with pytest.raises(Exception):
        TestDatabaseTable.load_archive()

    # try again with confirmation. This is also our last test so we can
    # delete the archive when we're done
    TestDatabaseTable.load_archive(
        confirm_override=True,
        delete_on_completion=True,
    )

    # Our test table doesn't have the remote_archive_link label set.
    with pytest.raises(Exception):
        TestDatabaseTable.load_remote_archive(
            confirm_override=True,
        )

    # now add the attribute and try again
    # NOTE: This is a live CDN! If my CDN server goes down, this test will fail
    TestDatabaseTable.remote_archive_link = (
        "https://archives.simmate.org/TestDatabaseTable-2022-02-08.zip"
    )
    TestDatabaseTable.load_remote_archive(
        confirm_override=True,
    )
