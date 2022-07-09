# -*- coding: utf-8 -*-

import os

import pytest

from simmate.command_line.database import database


@pytest.fixture  # BUG: is this test actually running...?
def test_database_reset(django_db_blocker, command_line_runner):

    # django-pytest does not let us to test the initial setup/configuration of the
    # database, so we need to do it within this context.
    #   https://pytest-django.readthedocs.io/en/latest/database.html#django-db-blocker
    with django_db_blocker.unblock():

        # reset the database
        result = command_line_runner.invoke(
            database, ["reset", "--confirm-delete", "--use-prebuilt=False"]
        )
        assert result.exit_code == 0

        # update the database
        result = command_line_runner.invoke(database, ["update"])
        assert result.exit_code == 0

        # OPTIMIZE: Is there a way to test this without downloading the large archive?
        # reset the database using a cloud archive
        # result = command_line_runner.invoke(
        #     database, ["reset", "--confirm-delete", "--use_prebuilt=True"]
        # )
        # assert result.exit_code == 0


@pytest.mark.django_db
def test_database_dump_and_load(command_line_runner):

    # dump the database to json
    result = command_line_runner.invoke(database, ["dumpdata"])
    assert result.exit_code == 0

    # load the database to json
    result = command_line_runner.invoke(database, ["loaddata"])
    assert result.exit_code == 0

    # delete the dump file
    os.remove("database_dump.json")
