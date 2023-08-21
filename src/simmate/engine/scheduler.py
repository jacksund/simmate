# -*- coding: utf-8 -*-

import importlib
import logging
import time

from rich import print
from schedule import run_pending

from simmate.configuration.django.settings import SIMMATE_APPS
from simmate.utilities import get_app_submodule

# This string is just something fancy to display in the console when the process
# starts up.
# This uses "Small Slant" from https://patorjk.com/software/taag/
HEADER_ART = r"""
=========================================================================
   _____                  __        ____    __          __     __       
  / __(_)_ _  __ _  ___ _/ /____   / __/___/ /  ___ ___/ /_ __/ /__ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_) _\ \/ __/ _ \/ -_) _  / // / / -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/ /___/\__/_//_/\__/\_,_/\_,_/_/\__/_/   
                                                                        
=========================================================================
"""


def register_app_schedules(apps_to_search: list[str] = SIMMATE_APPS):
    """
    Goes through a list of apps and imports the "schedules" module in each.
    By default, this will grab all installed SIMMATE_APPs
    """
    logging.info("Searching for registrations...")
    for app_name in apps_to_search:
        # check if there is a schedule module for this app and load it if so
        schedule_path = get_app_submodule(app_name, "schedules")
        if not schedule_path:
            continue  # skip to the next app
        # We use the python 'schedule' package, so simply importing these
        # modules is enough to register them.
        importlib.import_module(schedule_path)
        logging.info(f"Registered schedules for '{schedule_path}'")
    logging.info("Completed registrations :sparkles:")


def start_schedules():
    """
    Starts the main process for periodic tasks in each app's "schedules" module.

    NOTE: This is a "basic" alternative to scheduler systems such as Prefect.
    Here, only 1 task is ran at a time. So if you have a >1 hr task, this will
    block tasks schedules to run every minute until the longer task finishes.
    Furthermore, if you schedule a task to run at an exaction date/time, this
    scheduler may miss the start time due to other running tasks in front of it.
    Lastly, we "sleep" the scheduler every second, so scheduling tasks to run
    every <1s will not work as intended. The 1s sleep also means start times
    will have an error of up to 1s -- even when there's only one scheduled task.
    """

    # print the header in the console to let the user know the worker started
    print("[bold cyan]" + HEADER_ART)

    register_app_schedules()

    logging.info("Starting schedules...")
    while True:  # Run indefinitely
        run_pending()
        time.sleep(1)  # save some CPU time by sleeping for an extra second
