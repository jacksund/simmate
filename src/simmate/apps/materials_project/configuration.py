# -*- coding: utf-8 -*-

from simmate.apps.bader.configuration import test_config as test_bader_config
from simmate.apps.vasp.configuration import test_config as test_vasp_config
from simmate.configuration.utilities import check_app_reg, show_test_results


def test_config(run_calcs: bool = False):
    """
    Checks to see if Material Project App is configured correctly
    """

    # 1 - check that Simmate app is registered
    is_registered = check_app_reg("simmate.apps.configs.BadelfConfig")

    # 2 - check app dependancies
    has_vasp = test_vasp_config()
    has_bader = test_bader_config()

    # 3 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 4 - read out result of all tests
    passed_all = bool(is_registered and has_bader and has_vasp)
    show_test_results("BadELF", passed_all)
