"""
This defines commands for managing your Simmate configuration settings. All commands are
accessible through the "simmate config" command.
"""

import importlib
from pathlib import Path

import typer

from simmate.command_line.utilities import AlphabeticalGroup
from simmate.utils import get_app_submodule, logger

config_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)


def _get_app_configs() -> dict[str, str]:
    """
    Maps each built-in app's short name to its config path
    (e.g. `{"chembl": "simmate.apps.configs.ChemblConfig", ...}`).
    """
    from simmate.apps import configs

    return {
        config.name.split(".")[-1]: f"simmate.apps.configs.{config.__name__}"
        for config in vars(configs).values()
        if isinstance(config, type) and config.__module__ == configs.__name__
    }


@config_app.callback(no_args_is_help=True)
def config():
    """
    Commands for managing Simmate settings, including viewing, updating, and testing
    app configurations.
    """


@config_app.command()
def write(
    filename: Path = typer.Option(
        None,
        help="The filename (including path) to write settings to. Defaults to `simmate_settings.yaml` in the current directory.",
    ),
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
    ),
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

    if custom:
        settings.add_apps_and_update([app_name])
        return

    app_configs = _get_app_configs()
    if app_name not in app_configs:
        # The user may have mistyped. We don't want to add a line to the
        # settings file only for them to have to figure out how to delete it
        logger.warning(
            f"'{app_name}' is an unknown app. If you are using a custom app, "
            "please add the tag '--custom'. If this message is unexpected, "
            "check your command and app name for typos."
        )
        return

    # some apps need others installed alongside them
    app_dependencies = {
        "evolution": ["vasp"],  # TODO: deprec app dependency
        "materials_project": ["vasp", "bader"],
        "warren_lab": ["vasp", "baderkit"],
    }
    app_names = [*app_dependencies.get(app_name, []), app_name]
    settings.add_apps_and_update([app_configs[name] for name in app_names])


@config_app.command()
def update(
    config_update: str = typer.Argument(
        ...,
        metavar="CONFIG_UPDATE",
        help="The setting to update using dot-notation (e.g., 'database.backend=postgresql').",
    ),
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
    ),
):
    """
    Validates the configuration of a specified app (e.g., checking for installed
    software like VASP).
    """

    # apps opt into this command by adding a `config.py` with a `test_config` fxn
    app_configs = _get_app_configs()
    config_module = (
        get_app_submodule(app_configs[app_name], "config")
        if app_name in app_configs
        else None
    )
    if not config_module:
        logger.warning(f"Unknown app (or no tests exist): {app_name}")
        raise typer.Exit(code=1)

    passed = importlib.import_module(config_module).test_config()

    if not passed:
        raise typer.Exit(code=1)
