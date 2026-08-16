# -*- coding: utf-8 -*-

import pytest

from simmate.website.test_app.models import TestDatabaseTable


@pytest.mark.django_db
def test_database_table():
    # add a row
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()

    # check name
    assert x.table_name == x.__class__.__name__


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
def test_archive(tmp_path):
    # add sample rows
    x = TestDatabaseTable(column1=True, column2=3.14)
    x.save()
    y = TestDatabaseTable(column1=False, column2=-3.14)
    y.save()

    archive_filename = tmp_path / "test_table.zip"

    # Also try to load an archive that doesn't exist yet
    with pytest.raises(Exception):
        TestDatabaseTable.load_archive(filename=archive_filename)

    # write to a file
    TestDatabaseTable.objects.to_archive(filename=archive_filename)

    # reload the archive. This is also our last test so we can
    # delete the archive when we're done
    TestDatabaseTable.load_archive(
        filename=archive_filename,
        delete_on_completion=True,
    )

    # Our test table doesn't have the remote_archive_link label set.
    with pytest.raises(Exception):
        TestDatabaseTable.load_remote_archive()

    # now add the attribute and try again
    # NOTE: This is a live CDN! If my CDN server goes down, this test will fail.
    # This is also commonly blocked by CDNs when running from GitHub CI (HTTP 403)
    # TestDatabaseTable.remote_archive_link = (
    #     "https://assets.simmate.org/TestDatabaseTable-2022-02-08.zip"
    # )
    # TestDatabaseTable.load_remote_archive()
