# -*- coding: utf-8 -*-

import pytest

from simmate.command_line.compute import compute_app


@pytest.mark.django_db
def test_start_worker_cli(command_line_runner):
    # dump the database to json
    result = command_line_runner.invoke(
        compute_app,
        ["start-singleflow-worker"],
    )

    assert result.exit_code == 0

    # load the database to json
    result = command_line_runner.invoke(
        compute_app,
        ["start-worker", "--nitems-max", "1", "--close-on-empty-queue"],
    )
    assert result.exit_code == 0
