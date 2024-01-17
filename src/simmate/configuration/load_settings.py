import logging
import os
from functools import cached_property
from pathlib import Path

import yaml

import simmate
from simmate import website  # needed to specify location of built-in apps
from simmate.utilities import (
    deep_update,
    dotdict,
    get_conda_env,
    get_directory,
    str_to_datatype,
)


class SimmateSettings:
    """
    Configures Simmate settings
    """

    # TODO: consider using pydantic instead. I don't do this yet because of some
    # default values are dynamic and co-dependent, but I should revisit in the
    # future:
    #   https://github.com/pydantic/pydantic/issues/866

    # -------------------------------------------------------------------------

    @cached_property
    def final_settings(self) -> dict:
        """
        The final settings built from user-supplied settings and all defaults
        """
        settings = deep_update(
            default_dict=self.default_settings.copy(),
            override_dict=self.user_settings.copy(),
        )

        # clean variables
        # TODO: handle database.url input
        # TODO: use_docker inputs
        # CSRF_TRUSTED_ORIGINS = .split(",")
        # ALLOWED_HOSTS = .split(",")

        # REQUIRE_LOGIN = os.getenv("REQUIRE_LOGIN", "False") == "True"
        # # when setting REQUIRE_INTERNAL_LOGIN, set it to the allauth provider type
        # # (such as "microsoft")
        # REQUIRE_LOGIN_INTERNAL = os.getenv("REQUIRE_LOGIN_INTERNAL", "False")
        # if REQUIRE_LOGIN_INTERNAL == "False":
        #     REQUIRE_LOGIN_INTERNAL = False
        # else:
        #     assert REQUIRE_LOGIN_INTERNAL in ["microsoft", "google"]
        #     REQUIRE_LOGIN = True
        # # example: r'/apps/spotfire(.*)$'
        # REQUIRE_LOGIN_EXCEPTIONS = [
        #     e for e in os.getenv("REQUIRE_LOGIN_EXCEPTIONS", "").split(";") if e
        # ]
        # LOGIN_MESSAGE = os.getenv("LOGIN_MESSAGE", "")

        # Run compatibility checks (e.g. use_docker requires a 'docker run' cmd)
        # TODO

        return settings

    def __getattr__(self, name: str):
        """
        Makes all settings accessible as properties.

        This handles how `getattr(self, "example")` or `self.example` behaves
        when `example` is not actually defined.
        """
        if name not in self.final_settings.keys():
            raise Exception(f"Unknown property or setting: {name}")

        setting = self.final_settings.get(name, None)

        # if the property accessed is a dictionary, then we make it a dotdict
        # so that we can perform recursive dot access
        if isinstance(setting, dict):
            return dotdict(setting)
        else:
            return setting

    def write_settings(self, filename: Path = None):
        """
        Writes the final simmate settings to yaml file
        """
        if not filename:
            filename = (
                settings.config_directory / f"_{settings.conda_env}-settings.yaml"
            )

        logging.info(f"Writing settings to: '{filename}'")
        with filename.open("w") as file:
            content = yaml.dump(settings.final_settings)
            file.write(content)

    def show_settings(self, user_only: bool = False):
        """
        Takes the final simmate settings and prints them in a yaml format that is
        easier to read.
        """
        settings_to_print = self.final_settings if not user_only else self.user_settings
        print(yaml.dump(settings_to_print))

    # -------------------------------------------------------------------------

    @cached_property
    def default_settings(self) -> dict:
        """
        The default settings for Simmate.

        Note that some of these settings (such as the database name) are
        determined dynamically, so default may vary across different
        simmate installations.

        Further, some settings update the default for others. An example of this
        is `use_docker` for Quantum Espresso, which will also change the
        `default_command` for this app.
        """
        return {
            "version": simmate.__version__,
            "apps": [
                "simmate.workflows.configs.BaseWorkflowsConfig",
                "simmate.apps.configs.QuantumEspressoConfig",
                "simmate.apps.configs.VaspConfig",
                "simmate.apps.configs.BaderConfig",
                "simmate.apps.configs.EvolutionConfig",
                "simmate.apps.configs.MaterialsProjectConfig",
                # These apps may become defaults in the future:
                # "simmate.apps.configs.BadelfConfig",
                # "simmate.apps.configs.CleaseConfig",
                # "simmate.apps.configs.WarrenLabConfig",
            ],
            "database": self._default_database,
            "website": {
                # Sometimes we lock down the website to registered/approved users.
                # By default, we allow anonymous users to explore because this makes things like
                # REST API calls much easier for them. In special cases, such as industry, we
                # ONLY let users sign in via a specific allauth endpoint. An example of this
                # is Corteva limiting users to those approved via their Microsoft auth.
                "require_login": False,
                "require_login_internal": False,
                "require_login_exceptions": [],
                "login_message": None,
                # These allow server maintainers to override the homepage and profile views, which
                # is important if they involve loading custom apps/models for their templates.
                "home_view": None,
                "profile_view": None,
                "data": [
                    "simmate.database.third_parties.AflowPrototype",
                    # "simmate.database.third_parties.AflowStructure",  # Not allowed yet
                    "simmate.database.third_parties.CodStructure",
                    "simmate.database.third_parties.JarvisStructure",
                    "simmate.database.third_parties.MatprojStructure",
                    "simmate.database.third_parties.OqmdStructure",
                ],
                "social_oauth": {
                    "google": {"client_id": None, "secret": None},
                    "microsoft": {"client_id": None, "secret": None},
                    "github": {"client_id": None, "secret": None},
                },
                # django extras
                "debug": False,
                "allowed_hosts": ["127.0.0.1", "localhost"],
                # BUG-FIX: Django-unicorn ajax requests sometimes come from the server-side
                # ingress (url for k8s) or a nginx load balancer. To get past a 403 forbidden
                # result, we need to sometimes specify allowed origins for csrf.
                "csrf_trusted_origins": ["http://localhost"],
                # Keep the secret key used in production secret!
                # !!! I removed get_random_secret_key() so I don't have to sign out every time
                # while testing my server. I may change this back in the future.
                # from django.core.management.utils import get_random_secret_key
                "secret_key": "pocj6cunub4zi31r02vr5*5a2c(+_a0+(zsswa7fmus^o78v)r",
                # Settings for sending automated emails.
                # For example, this can be set up for GMail by...
                #   1. enabling IMAP (in gmail settings)
                #   2. Having 2-factor auth turned on
                #   3. Adding an App Password (in account settings)
                "email": {
                    "backend": "django.core.mail.backends.smtp.EmailBackend",  # this is the default
                    "host": "smtp.gmail.com",  # or outlook.office365.com
                    "port": 587,
                    "use_tls": False,
                    "host_user": "",
                    "host_password": "",
                    "from_email": "simmate.team@gmail.com",
                    "timeout": 5,
                    "subject_prefix": "[Simmate] ",
                    "account_verification": "none",  # when creating new accounts
                },
                # These people get an email when DEBUG=False
                "admins": [
                    ("jacksund", "jacksundberg123@gmail.com"),
                    ("jacksund-corteva", "jack.sundberg@corteva.com"),
                ],
            },
            # app-specific configs
            # TODO: consider moving these to the respective apps
            "vasp": {
                "default_command": "vasp_std > vasp.out",
                "parallelization": {
                    "ncore": None,
                    "kpar": None,
                },
            },
            "quantum_espresso": {
                "default_command": "pw.x < pwscf.in > pw-scf.out",
                "use_docker": False,
            },
        }

    @cached_property
    def _default_database(self) -> Path:
        # if the user is in the (base) env or not using conda, then we will have a
        # value of "-database.sqlite3", which why we need strip() here.
        db_filename = (
            self.config_directory / f"{self.conda_env}-database.sqlite3".strip("-")
        )
        return {
            "engine": "django.db.backends.sqlite3",
            "name": db_filename,
        }

    @cached_property
    def database_backend(self) -> str:  # was... DATABASE_BACKEND
        if self.database.engine == "django.db.backends.sqlite3":
            return "sqlite3"
        elif self.database.engine == "django.db.backends.postgresql":
            return "postgresql"
        else:
            return "unknown"

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
        settings_file = self.config_directory / f"{self.conda_env}-settings.yaml"
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

            # skip simmate settings that are set via a helm chart or docker
            # container, but not updated by user. All of these cloud deployments
            # use "__skip__" as the default value
            if value == "__skip__":
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
            user_settings = deep_update(user_settings, cleaned_setting)

        return user_settings

    # -------------------------------------------------------------------------

    # Fixed settings that are automatically set

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
        "SIMMATE__APPS": list[str],
        "SIMMATE__DATABASE__ENGINE": str,
        "SIMMATE__DATABASE__HOST": str,
        "SIMMATE__DATABASE__NAME": str,
        "SIMMATE__DATABASE__USER": str,
        "SIMMATE__DATABASE__PASSWORD": str,
        "SIMMATE__DATABASE__PORT": int,
        "SIMMATE__WEBSITE__ALLOWED_HOSTS": list[str],
        "SIMMATE__WEBSITE__CSRF_TRUSTED_ORIGINS": list[str],
        "SIMMATE__WEBSITE__DATA": list[str],
        "SIMMATE__WEBSITE__DEBUG": bool,
        "SIMMATE__WEBSITE__EMAILS__FROM_EMAIL": str,
        "SIMMATE__WEBSITE__EMAILS__HOST": str,
        "SIMMATE__WEBSITE__EMAILS__PORT": int,
        "SIMMATE__WEBSITE__EMAILS__TIMEOUT": int,  # or float...?
        "SIMMATE__WEBSITE__HOME_VIEW": str,
        "SIMMATE__WEBSITE__LOGIN_MESSAGE": str,
        "SIMMATE__WEBSITE__PROFILE_VIEW": str,
        "SIMMATE__WEBSITE__REQUIRE_LOGIN": bool,
        "SIMMATE__WEBSITE__REQUIRE_LOGIN_EXCEPTIONS": list[str],
        "SIMMATE__WEBSITE__REQUIRE_LOGIN_INTERNAL": bool,
        "SIMMATE__WEBSITE__SOCIAL_OAUTH__MICROSOFT__CLIENT_ID": str,
        "SIMMATE__WEBSITE__SOCIAL_OAUTH__MICROSOFT__SECRET": str,
    }


# initialize all settings
settings = SimmateSettings()
