# -*- coding: utf-8 -*-

from simmate.configuration import settings
from simmate.configuration.utilities import (
    check_app_reg,
    check_command_exists,
    show_test_results,
)


def test_config(run_calcs: bool = False):
    """
    Checks to see if Bader is configured correctly
    """

    # 1 - check that Simmate app is registered
    is_registered = check_app_reg("simmate.apps.configs.BaderConfig")

    # 2 - check for command
    use_docker = settings.quantum_espresso.docker.enable
    command = "bader" if not use_docker else "docker"
    found_command = check_command_exists(command)

    # 3 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 4 - read out result of all tests
    passed_all = bool(is_registered and found_command)
    show_test_results("Bader", passed_all)
