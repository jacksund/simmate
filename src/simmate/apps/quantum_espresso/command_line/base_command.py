# -*- coding: utf-8 -*-

"""
This defines the base "simmate-qe" command that all other commands stem from.
"""

import typer

from simmate.apps.quantum_espresso.command_line.setup import setup_app

qe_app = typer.Typer(rich_markup_mode="markdown")


@qe_app.callback(no_args_is_help=True)
def base_command():
    """
    A collection of utilities to help work with VASP
    """
    # When we call the command "simmate-vasp" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate_vasp.command()"
    # to decide what to do from there.
    pass


@qe_app.command()
def test(run_calcs: bool = False):
    """
    Checks to see if Quantum Espresso is configured correctly
    """
    import logging
    import shutil

    from simmate.configuration.django.settings import APPLICATIONS_YAML, INSTALLED_APPS

    # true until proven otherwise
    passed_all = True

    # 1 - check that QE Simmate app is registered
    app_name = "simmate.apps.configs.QuantumEspressoConfig"
    is_registered = app_name in INSTALLED_APPS
    if is_registered:
        logging.info("Quantum Espresso app is registered :heavy_check_mark:")
    else:
        logging.warning(
            "You must have the Quantum Espresso app registered with Simmate. "
            f"To do this, add '{app_name}' to {APPLICATIONS_YAML}"
        )
        passed_all = False

    # 2 - check for pw.x command
    from simmate.apps.quantum_espresso.settings import SIMMATE_QE_DOCKER

    command = "pw.x" if not SIMMATE_QE_DOCKER else "docker"
    if shutil.which(command):
        logging.info("PW-SCF command found ('pw.x') :heavy_check_mark:")
    else:
        logging.warning(
            "You must have QE (PWSCF) installed and in the PATH, but "
            "we were unable to detect the `pw.x` command."
        )
        passed_all = False

    # 3 - check for psuedopotentials
    from simmate.apps.quantum_espresso.inputs.potentials_sssp import check_psuedo_setup

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
        raise typer.Exit(code=1)


# All commands are organized into other files, so we need to manually register
# them to our base "simmate-qe" command here.
qe_app.add_typer(setup_app, name="setup")
