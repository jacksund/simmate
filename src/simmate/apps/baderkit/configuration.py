# -*- coding: utf-8 -*-

from simmate.configuration.utilities import check_app_reg, show_test_results, check_command_exists


def test_config(run_calcs: bool = False):
    """
    Checks to see if Baderkit is configured correctly
    """
    # 1 - check that Simmate app is registered
    is_registered = check_app_reg("simmate.apps.configs.BaderkitConfig")

    # 2 - check app dependancies
    has_bader = check_command_exists("baderkit")

    # 3 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 4 - read out result of all tests
    passed_all = bool(is_registered and has_bader)
    show_test_results("Baderkit", passed_all)