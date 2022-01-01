# -*- coding: utf-8 -*-

import os

from click.testing import CliRunner
from simmate.command_line.database import database


def test_database():
    # make the dummy terminal
    runner = CliRunner()

    # reset the database
    result = runner.invoke(database, ["reset", "--confirm-delete"])
    assert result.exit_code == 0

    # update the database
    result = runner.invoke(database, ["update"])
    assert result.exit_code == 0

    # dump the database to json
    result = runner.invoke(database, ["dumpdata"])
    assert result.exit_code == 0

    # load the database to json
    result = runner.invoke(database, ["loaddata"])
    assert result.exit_code == 0

    # delete the dump file
    os.remove("database_dump.json")
