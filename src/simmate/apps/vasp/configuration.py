# -*- coding: utf-8 -*-

import logging

from simmate.apps.vasp.inputs.potcar_mappings import FOLDER_MAPPINGS
from simmate.configuration.utilities import (
    check_app_reg,
    check_command_exists,
    show_test_results,
)


def test_config(run_calcs: bool = False):
    """
    Checks to see if VASP is configured correctly
    """

    # 1 - check that VASP Simmate app is registered
    is_registered = check_app_reg("simmate.apps.configs.VaspConfig")

    # 2 - check for vasp command
    found_command = check_command_exists("vasp_std")

    # 3 - check for vasp potcars
    has_potcars = True
    for potential, folder in FOLDER_MAPPINGS.items():
        if folder.exists():
            logging.info(f"{potential} POTCARS found :heavy_check_mark:")
        else:
            logging.warning(
                f"{potential} POTCARS not found. These should be placed at... "
                f"'{folder}'"
            )
            has_potcars = False

    # 4 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 5 - read out result of all tests
    passed_all = bool(is_registered and found_command and has_potcars)
    show_test_results("VASP", passed_all)
