# -*- coding: utf-8 -*-

from simmate.command_line.base_command import simmate_app


def test_base_command(command_line_runner):
    result = command_line_runner.invoke(simmate_app, ["--help"])
    assert result.exit_code == 0
