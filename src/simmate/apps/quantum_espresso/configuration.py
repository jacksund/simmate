# -*- coding: utf-8 -*-

import logging
import shutil

from simmate.apps.quantum_espresso.inputs.potentials_sssp import check_psuedo_setup
from simmate.configuration import settings


def test_config(run_calcs: bool = False):
    """
    Checks to see if Quantum Espresso is configured correctly
    """

    # true until proven otherwise
    passed_all = True

    # 1 - check that QE Simmate app is registered
    app_name = "simmate.apps.configs.QuantumEspressoConfig"
    is_registered = app_name in settings.apps
    if is_registered:
        logging.info("Quantum Espresso app is registered :heavy_check_mark:")
    else:
        logging.warning("You must have the Quantum Espresso app registered")
        passed_all = False

    # 2 - check for pw.x command (or docker)
    use_docker = settings.quantum_espresso.docker.enable
    command = "pw.x" if not use_docker else "docker"
    if command == "pw.x":
        if shutil.which(command):
            logging.info("PW-SCF command found ('pw.x') :heavy_check_mark:")
        else:
            logging.warning(
                "You must have QE (PWSCF) installed and in the PATH, but "
                "we were unable to detect the `pw.x` command."
            )
            passed_all = False
    elif command == "docker":
        # TODO: Move this to a utility
        if shutil.which(command):
            logging.info("Docker command found ('docker') :heavy_check_mark:")
        else:
            logging.warning(
                "You must have Docker installed and in the PATH, but "
                "we were unable to detect the `docker` command."
            )
            passed_all = False

    # 3 - check for psuedopotentials
    is_passed = check_psuedo_setup()

    if is_passed:
        logging.info("Psuedopotentials (SSSP) found :heavy_check_mark:")
    else:
        logging.warning("Psuedopotentials (SSSP) not found.")
        passed_all = False

    # 4 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 5 - read out result of all tests
    if passed_all:
        logging.info(
            "All Quantum Espresso config checks passed! :fire::fire::fire::rocket:"
        )
    else:
        logging.critical(":warning:  At least one check failed. See above :warning:")
        # raise typer.Exit(code=1)  # TODO: should I raise error or return False?
