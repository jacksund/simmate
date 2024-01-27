# -*- coding: utf-8 -*-

import logging

from simmate.apps.quantum_espresso.inputs.potentials_sssp import check_psuedo_setup
from simmate.configuration import settings
from simmate.configuration.utilities import (
    check_app_reg,
    check_command_exists,
    show_test_results,
)


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

    # 3 - check for psuedopotentials
    has_puedos = check_psuedo_setup()
    if has_puedos:
        logging.info("Psuedopotentials (SSSP) found :heavy_check_mark:")
    else:
        logging.warning("Psuedopotentials (SSSP) not found.")

    # 4 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 5 - read out result of all tests
    passed_all = bool(is_registered and found_command and has_puedos)
    show_test_results("Quantum Espresso", passed_all)
