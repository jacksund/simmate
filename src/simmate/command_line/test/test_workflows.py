# -*- coding: utf-8 -*-

from click.testing import CliRunner
from simmate.command_line.workflows import workflows


def test_database():
    # make the dummy terminal
    runner = CliRunner()

    # list the workflows
    result = runner.invoke(workflows, ["list-all"])
    assert result.exit_code == 0

    # list the config for one workflow
    result = runner.invoke(workflows, ["show-config", "static-energy/mit"])
    assert result.exit_code == 0


# How will I mock the testing of VASP? It will require the database to be configured.
# Also I need Structure fixtures.
# TODO: test setup_only, run, run_cloud
