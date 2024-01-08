import os
from functools import cached_property
from pathlib import Path

import yaml

from simmate import website  # needed to specify location of built-in apps
from simmate.utilities import get_conda_env, get_directory, str_to_datatype


class SimmateSettings:
    # def __getattr__(self, name):
    #     return self.config.get(name, None)
    # TODO: grabs from all_settings

    # -------------------------------------------------------------------------

    @cached_property
    def all_settings(self) -> dict:
        settings = self.default_settings.copy()
        user_settings = self.user_settings.copy()
        settings.update(user_settings)
        return settings

    @cached_property
    def default_settings(self):
        return {}

    # -------------------------------------------------------------------------

    @cached_property
    def user_settings(self) -> dict:
        """
        A dictionary of keys-values that the user has set via the `setting_source`
        """
        source = self.settings_source

        # no user settings
        if not source:
            return {}
        # a yaml file
        elif isinstance(source, Path):
            with source.open() as file:
                return yaml.full_load(file)
        # environment variables
        elif source == "environment variables":
            return self._get_env_settings()

    @cached_property
    def settings_source(self):
        """
        Where the settings are being loading from.

        There are several options for configuring settings that we check for, in order
        of priority:

        1. environment variables
        2. settings.yaml
        3. {conda env}-settings.yaml
        4. nothing (use the default)

        We do NOT allow for a mixture of these. This because tracking down where
        a setting came from would be tricky if there are both environment variables
        and settings files being used.
        """

        # 1. check if using environment variables
        prefix = "SIMMATE__"
        env_vars = dict(os.environ)
        if any(var.startswith(prefix) for var in env_vars.keys()):
            return "environment variables"

        # 2. settings.yaml file
        settings_file = self.config_directory / "settings.yaml"
        if settings_file.exists():
            return settings_file

        # 3. my_env-settings.yaml file
        settings_file = self.config_directory / "{self.conda_env}-settings.yaml"
        if settings_file.exists():
            return settings_file

        # 4. Using 100% defaults
        return None

    def _get_env_settings(self) -> dict:
        """
        Parses all 'SIMMATE__' settings from available environment variables
        """
        
        # grab all variables associated with simmate and break down the variables
        # into a "normal" dictionary with proper python types
        # For example:
        #   {"SIMMATE__WEBSITE___REQUIRE_LOGIN": "true"}
        #   ...into..
        #   {"website": {"require_login": True}}
        user_settings = {}
        for key, value in dict(os.environ).items():
            # skip non-simmate settings
            if not key.startswith("SIMMATE__"):
                continue

            # Convert the value to the proper python type.
            value_cleaned = str_to_datatype(
                parameter=key,
                value=value,
                type_mappings=self._input_mappings,
            )
            # OPTIMIZE: There might be better ways to do this, such as
            # inspecting the attribute. Example with 'conda_env':
            #   SimmateSettings.conda_env.func.__annotations__["return"]

            # split the variable name into basic keys. Note, how we
            # throw out the first key because it is always "simmate".
            # We also convert to lowercase
            components = [c.lower() for c in key.split("__")[1:]]

            # reformat dictionary
            cleaned_setting = {components[-1]: value_cleaned}
            for sub_key in reversed(components[:-1]):
                cleaned_setting = {sub_key: cleaned_setting}

            # add to final set
            user_settings.update(cleaned_setting)

        return user_settings

    # -------------------------------------------------------------------------

    @cached_property
    def conda_env(self) -> str:
        """
        Name of the conda environment being used.

        Some settings depend on the conda env name. This makes switching
        between different databases and settings as easy as activating different
        conda environments
        """
        return get_conda_env()

    @cached_property
    def config_directory(self) -> Path:
        """
        We check for all settings in the user's home directory and in a
        folder named "~/simmate/".
        For windows, this would be something like...
          C:\\Users\\exampleuser\\simmate\\extra_applications
        """
        # we use `get_directory` in order to create the folder if it does not exist.
        return get_directory(Path.home() / "simmate")

    @cached_property
    def django_directory(self) -> str:
        """
        Location of the `simmate.website` module & django "base"

        This directory is where simmate.website is located and helps us indicate
        where things like our templates or static files are located. We find this
        by looking at the import path to see where python installed it.
        """
        return Path(website.__file__).absolute().parent

    # -------------------------------------------------------------------------

    # OPTIMIZE: this is only used in the _get_env_settings method and should
    # depreciated in favor of type-inspecting
    _input_mappings: dict = {
        "SIMMATE__WEBSITE__REQUIRE_LOGIN": bool,
    }


# Usage example
settings = SimmateSettings()
print(settings.settings_source)
print(settings.user_settings)
print(settings.all_settings)
