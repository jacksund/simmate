# -*- coding: utf-8 -*-

"""
This defines the base "simmate-vasp" command that all other commands stem from.
"""

import typer

from simmate.apps.vasp.command_line.inputs import inputs_app
from simmate.apps.vasp.command_line.plot import plot_app

vasp_app = typer.Typer(rich_markup_mode="markdown")


@vasp_app.callback(no_args_is_help=True)
def base_command():
    """
    A collection of utilities to help work with VASP
    """
    # When we call the command "simmate-vasp" this is where we start, and it then
    # looks for all other functions that have the decorator "@simmate_vasp.command()"
    # to decide what to do from there.
    pass


@vasp_app.command()
def test(run_calcs: bool = False):
    """
    Checks to see if VASP is configured correctly
    """
    import logging
    import shutil

    from simmate.configuration.django.settings import APPLICATIONS_YAML, INSTALLED_APPS

    # true until proven otherwise
    passed_all = True

    # 1 - check that VASP Simmate app is registered
    app_name = "simmate.apps.configs.VaspConfig"
    is_registered = app_name in INSTALLED_APPS
    if is_registered:
        logging.info("VASP app is registered :heavy_check_mark:")
    else:
        logging.warning(
            "You must have the VASP app registered with Simmate. "
            f"To do this, add '{app_name}' to {APPLICATIONS_YAML}"
        )
        passed_all = False

    # 2 - check for vasp command
    command = "vasp_std"
    if shutil.which(command):
        logging.info("VASP command found ('vasp_std') :heavy_check_mark:")
    else:
        logging.warning(
            "You must have VASP installed and in the PATH, but "
            "we were unable to detect the `vasp_std` command."
        )
        passed_all = False

    # 3 - check for vasp potcars
    from simmate.apps.vasp.inputs.potcar_mappings import FOLDER_MAPPINGS

    for potential, folder in FOLDER_MAPPINGS.items():
        if folder.exists():
            logging.info(f"{potential} POTCARS found :heavy_check_mark:")
        else:
            logging.warning(
                f"{potential} POTCARS not found. These should be placed at... "
                f"'{folder}'"
            )
            passed_all = False

    # 4 - run some sample workflows
    if run_calcs:
        raise NotImplementedError("This test has not been added yet.")

    # 5 - read out result of all tests
    if passed_all:
        logging.info("All VASP config checks passed! :fire::fire::fire::rocket:")
    else:
        logging.critical(":warning:  At least one check failed. See above :warning:")
        raise typer.Exit(code=1)


# All commands are organized into other files, so we need to manually register
# them to our base "simmate-vasp" command here.
vasp_app.add_typer(inputs_app, name="inputs")
vasp_app.add_typer(plot_app, name="plot")
