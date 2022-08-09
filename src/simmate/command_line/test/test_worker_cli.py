# -*- coding: utf-8 -*-

import pytest

from simmate.command_line.workflow_engine import workflow_engine


@pytest.mark.django_db
def test_database_dump_and_load(command_line_runner):

    # dump the database to json
    result = command_line_runner.invoke(workflow_engine, ["start-singleflow-worker"])
    assert result.exit_code == 0

    # load the database to json
    result = command_line_runner.invoke(
        workflow_engine, ["start-worker", "-n", "1", "-e", "true"]
    )
    assert result.exit_code == 0
