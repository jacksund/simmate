# -*- coding: utf-8 -*-

import logging
import shutil

from simmate.configuration import settings


def check_app_reg(app_config_str: str) -> bool:
    """
    Checks to see if an app Config is present in Simmate settings
    """
    is_registered = app_config_str in settings.apps
    app_short = app_config_str.split(".")[-1]
    if is_registered:
        logging.info(f"{app_short} is registered :heavy_check_mark:")
        return True
    else:
        logging.warning(f"You must have {app_short} registered")
        return False


def check_command_exists(command: str) -> bool:
    """
    Checks to see if a command is present in PATH
    """
    if shutil.which(command):
        logging.info(f"'{command}' command found :heavy_check_mark:")
        return True
    else:
        logging.warning(
            f"we were unable to detect the '{command}' command."
            f"You must have '{command}' installed and in the PATH, or enable "
            "docker for this program."
        )
        return True


def show_test_results(app_name: str, passed: bool):
    """
    Simple utility that logs a message for users based on whether configuration
    checks pass
    """
    if passed:
        logging.info(f"All {app_name} config checks passed")
        return True
    else:
        logging.critical(f":warning: At least one {app_name} check failed :warning:")
        return False
