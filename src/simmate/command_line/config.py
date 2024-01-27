# -*- coding: utf-8 -*-

"""
This defines commands for managing your Simmate configuration settings. All commands are 
accessible through the "simmate config" command.
"""

import logging
from pathlib import Path

import typer

config_app = typer.Typer(rich_markup_mode="markdown")


@config_app.callback(no_args_is_help=True)
def utilities():
    """
    A group of commands for managing Simmate settings
    """
    pass


@config_app.command()
def write(filename: Path = None):
    """
    Writes the final simmate settings to yaml file

    - `filename`: file name to write settings to
    """

    from simmate.configuration import settings

    settings.write_settings(filename=filename)


@config_app.command()
def show(user_only: bool = False):
    """
    Takes the final simmate settings and prints them in a yaml format that is
    easier to read.
    """
    from simmate.configuration import settings

    settings.show_settings(user_only=user_only)


@config_app.command()
def add(app_name: str):
    """
    Adds a specified Simmate app to the list of registered apps
    """

    from simmate.configuration import settings

    if app_name == "badelf":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.BaderConfig",
            ]
        )
    elif app_name == "bader":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.BaderConfig",
            ]
        )
    elif app_name == "clease":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.CleaseConfig",
            ]
        )
    elif app_name == "evolution":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.VaspConfig",  # TODO: deprec app dependency
                "simmate.apps.configs.EvolutionConfig",
            ]
        )
    elif app_name == "materials_project":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.VaspConfig",
                "simmate.apps.configs.BaderConfig",
                "simmate.apps.configs.MaterialsProjectConfig",
            ]
        )
    elif app_name == "quantum_espresso":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.QuantumEspressoConfig",
            ]
        )
    elif app_name == "vasp":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.VaspConfig",
            ]
        )
    elif app_name == "warren_lab":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.VaspConfig",
                "simmate.apps.configs.BaderConfig",
                "simmate.apps.configs.BadelfConfig",
                "simmate.apps.configs.WarrenLabConfig",
            ]
        )
    else:
        # user is giving a custom app
        settings.add_apps_and_update([app_name])


@config_app.command()
def update(config: str):
    """
    Updates Simmate settings using dot-notation
    """

    from simmate.configuration import settings

    config_cleaned = settings._parse_input(config)
    settings.write_updated_settings(config_cleaned)


@config_app.command()
def test(app_name: str):
    """
    Tests whether an app is properly configured
    """

    # OPTIMIZE: this code can be refactored and condensed. but it works for now

    if app_name == "badelf":
        from simmate.apps.bader.configuration import test_config

        passed = test_config()

    elif app_name == "bader":
        from simmate.apps.bader.configuration import test_config

        passed = test_config()

    elif app_name == "materials_project":
        from simmate.apps.materials_project.configuration import test_config

        passed = test_config()

    elif app_name == "quantum_espresso":
        from simmate.apps.quantum_espresso.configuration import test_config

        passed = test_config()

    elif app_name == "vasp":
        from simmate.apps.vasp.configuration import test_config

        passed = test_config()

    elif app_name == "warren_lab":
        from simmate.apps.warren_lab.configuration import test_config

        passed = test_config()

    else:
        logging.warning(f"Unknown app (or no tests exist): {app_name}")
        passed = False

    if not passed:
        raise typer.Exit(code=1)
