# -*- coding: utf-8 -*-

from click.testing import CliRunner
from simmate.command_line.base_command import simmate


def test_base_command():
    runner = CliRunner()
    result = runner.invoke(simmate)
    assert result.exit_code == 0
