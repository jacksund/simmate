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
def config():
    """
    Commands for managing Simmate settings, including viewing, updating, and testing
    app configurations.
    """
    pass


@config_app.command()
def write(
    filename: Path = typer.Option(
        None,
        help="The filename (including path) to write settings to. Defaults to `simmate_settings.yaml` in the current directory.",
    )
):
    """
    Writes the final Simmate configuration (including defaults) to a YAML file.
    """

    from simmate.config import settings

    settings.write_settings(filename=filename)


@config_app.command()
def show(
    user_only: bool = typer.Option(
        False,
        help="Only display settings that have been explicitly modified by the user. If false, all settings including defaults are shown.",
    )
):
    """
    Displays the final Simmate settings in an easy-to-read YAML format.
    """
    from simmate.config import settings

    settings.show_settings(user_only=user_only)


@config_app.command()
def add(
    app_name: str = typer.Argument(
        ...,
        help="The name of the app to register (e.g., 'vasp', 'materials_project').",
    ),
    custom: bool = typer.Option(
        False,
        help="Whether the app name refers to a custom Python module (e.g., 'my_custom_app.config.MyAppConfig').",
    ),
):
    """
    Adds a specified Simmate app to the list of registered apps in your configuration.
    """

    from simmate.config import settings

    if app_name == "aflow":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.AflowConfig",
            ]
        )
    elif app_name == "bader":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.BaderConfig",
            ]
        )
    elif app_name == "baderkit":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.BaderkitConfig",
            ]
        )
    elif app_name == "clease":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.CleaseConfig",
            ]
        )
    elif app_name == "cod":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.CodConfig",
            ]
        )
    elif app_name == "deepmd":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.DeepmdConfig",
            ]
        )
    elif app_name == "evolution":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.VaspConfig",  # TODO: deprec app dependency
                "simmate.apps.configs.EvolutionConfig",
            ]
        )
    elif app_name == "jarvis":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.JarvisConfig",
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
    elif app_name == "oqmd":
        settings.add_apps_and_update(
            [
                "simmate.apps.configs.OqmdConfig",
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
                "simmate.apps.configs.BaderkitConfig",
                "simmate.apps.configs.WarrenLabConfig",
            ]
        )
    elif app_name in [
        "rdkit",
        "bcpc",
        "cas_registry",
        "chembl",
        "chemspace",
        "cod",
        "emolecules",
        "enamine",
        "eppo_gd",
        "pdb",
    ]:
        logging.critical(
            "Molecular apps are not available yet! These will be available in the next simmate release (Summer 2025)"
        )
        return
    else:
        if not custom:
            # The user may have mistyped. We don't want to add a line to the
            # settings file only for them to have to figure out how to delete it
            logging.warning(
                f"'{app_name}' is an unknown app. If you are using a custom app, "
                "please add the tag '--custom'. If this message is unexpected, "
                "check your command and app name for typos."
            )
        else:
            # user is giving a custom app
            settings.add_apps_and_update([app_name])


@config_app.command()
def update(
    config_update: str = typer.Argument(
        ...,
        metavar="CONFIG_UPDATE",
        help="The setting to update using dot-notation (e.g., 'database.backend=postgresql').",
    )
):
    """
    Updates one or more Simmate settings using dot-notation and writes them to
    your settings file.
    """

    from simmate.config import settings

    config_cleaned = settings._parse_input(config_update)
    settings.write_updated_settings(config_cleaned)


@config_app.command()
def test(
    app_name: str = typer.Argument(
        ...,
        help="The name of the app to test configuration for.",
    )
):
    """
    Validates the configuration of a specified app (e.g., checking for installed
    software like VASP).
    """

    # OPTIMIZE: this code can be refactored and condensed. but it works for now

    if app_name == "bader":
        from simmate.apps.bader.config import test_config

        passed = test_config()

    elif app_name == "baderkit":
        from simmate.apps.baderkit.config import test_config

        passed = test_config()

    elif app_name == "materials_project":
        from simmate.apps.materials_project.config import test_config

        passed = test_config()

    elif app_name == "quantum_espresso":
        from simmate.apps.quantum_espresso.config import test_config

        passed = test_config()

    elif app_name == "vasp":
        from simmate.apps.vasp.config import test_config

        passed = test_config()

    elif app_name == "warren_lab":
        from simmate.apps.warren_lab.config import test_config

        passed = test_config()

    else:
        logging.warning(f"Unknown app (or no tests exist): {app_name}")
        passed = False

    if not passed:
        raise typer.Exit(code=1)
