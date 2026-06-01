# -*- coding: utf-8 -*-

import logging

from simmate.config import settings
from simmate.config.utils import (
    check_app_reg,
    check_command_exists,
    show_test_results,
)

from .inputs import check_pseudo_setup


def test_config(run_calcs: bool = False):
    """
    Checks to see if Quantum Espresso is configured correctly
    """

    # 1 - check that Simmate app is registered
    is_registered = check_app_reg("simmate.apps.configs.QuantumEspressoConfig")

    # 2 - check for command
    use_docker = settings.quantum_espresso.docker.enable
    command = "pw.x" if not use_docker else "docker"
    found_command = check_command_exists(command)

    # 3 - check for pseudopotentials
    has_pseudos = check_pseudo_setup()
    if has_pseudos:
        logging.info("Pseudopotentials (SSSP) found :heavy_check_mark:")
    else:
        logging.warning("Pseudopotentials (SSSP) not found.")

    # 4 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 5 - read out result of all tests
    passed_all = bool(is_registered and found_command and has_pseudos)
    show_test_results("Quantum Espresso", passed_all)
