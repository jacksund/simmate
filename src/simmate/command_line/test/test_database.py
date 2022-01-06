# -*- coding: utf-8 -*-

import os

import pytest
from click.testing import CliRunner

from simmate.command_line.database import database
from simmate.configuration.django.database import update_database


@pytest.mark.no_django_setup
def test_database_reset():

    # make the dummy terminal
    runner = CliRunner()

    # reset the database
    result = runner.invoke(database, ["reset", "--confirm-delete"])
    assert result.exit_code == 0

    # update the database
    result = runner.invoke(database, ["update"])
    assert result.exit_code == 0


@pytest.mark.django_db
def test_database_dump_and_load():

    # make sure all models are updated
    update_database()

    # make the dummy terminal
    runner = CliRunner()

    # dump the database to json
    result = runner.invoke(database, ["dumpdata"])
    assert result.exit_code == 0

    # load the database to json
    result = runner.invoke(database, ["loaddata"])
    assert result.exit_code == 0

    # delete the dump file
    os.remove("database_dump.json")
