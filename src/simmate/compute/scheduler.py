# -*- coding: utf-8 -*-

import datetime
import importlib
import logging
import time
from traceback import format_exc
from typing import Literal

import schedule as schedule_lib
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from rich import print
from schedule import Scheduler

from simmate.config import settings
from simmate.utils import get_app_submodule

from .executor import SimmateExecutor

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


class SimmateScheduler(Scheduler):
    """
    Starts the main process for periodic tasks in each app's "schedules" module.

    Scheduled tasks are submitted to the queue database as WorkItems, meaning
    the scheduler process itself never blocks. Heavy lifting is handled
    asynchronously by Simmate Workers.
    """

    def __init__(self, reschedule_on_failure=True):
        """
        If reschedule_on_failure is True, jobs will be rescheduled for their
        next run as if they had completed successfully. If False, they'll run
        on the next run_pending() tick.
        """
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    @classmethod
    def start(cls, sleep_step: float = 1):
        """
        Starts the main process for periodic tasks in each app's "schedules" module.

        Scheduled tasks are submitted to the queue database as WorkItems, meaning
        the scheduler process itself never blocks. Heavy lifting is handled
        asynchronously by Simmate Workers.
        """

        # TODO: consider parallel runs using threads, dask, or workers...
        # https://schedule.readthedocs.io/en/stable/parallel-execution.html

        # TODO: for error handling, read more at...
        # https://schedule.readthedocs.io/en/stable/exception-handling.html

        # print the header in the console to let the user know the worker started
        print("[bold cyan]" + HEADER_ART)

        # HACK-FIX:
        # Jobs will register to the default scheduler. We instead want to use
        # this custom class, so we patch the schedule module
        # https://github.com/dbader/schedule/blob/master/schedule/__init__.py#L801C1-L881C31
        import schedule

        schedule.default_scheduler = cls()

        # Now run the registration where the scheduler shortcuts will work
        cls._register_app_schedules()

        # And now run the infinite loop of schedules
        logging.info("Starting schedules...")
        while True:  # Run indefinitely
            schedule.run_pending()
            # save some CPU time by sleeping for an extra second
            time.sleep(sleep_step)

    @staticmethod
    def _register_app_schedules(apps_to_search: list[str] = settings.apps):
        """
        Goes through a list of apps and imports the "schedules" module in each.
        By default, this will grab all installed 'settings.apps'
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

    def _run_job(self, job):
        # This is a modified run method that catches failed jobs and optionally
        # sends an email alert on failure events

        try:
            super()._run_job(job)
        except Exception:
            # log errors but still continue
            error_msg = format_exc()
            logging.critical(error_msg)
            job.last_run = datetime.datetime.now()
            job._schedule_next_run()

            # if emails are configured, send an alert of the failure
            # TODO: maybe use SuperUserEmailHandler
            email = EmailMessage(
                subject="[SIMMATE] Scheduled job failure",
                body=error_msg,
                to=list(
                    User.objects.filter(
                        is_superuser=True,
                        is_active=True,
                        email__isnull=False,
                    ).values_list("email", flat=True)
                ),  # get admin emails
            )
            email.send(fail_silently=True)


def schedule(
    interval: Literal["minute", "hourly", "daily", "weekly"],
    at: str = None,
    tags: list[str] = ["simmate"],
    **job_kwargs,
):
    """
    Registers a function to be ran periodically.
    Rather than running the task in the main scheduler thread, this will submit
    the task as a WorkItem to the queue database so that workers can pick it up.
    """

    def decorator(func):
        # Determine how to submit the object
        def submit_to_worker():
            logging.info(
                f"Submitting scheduled task: {getattr(func, '__name__', str(func))}"
            )
            SimmateExecutor.submit(func, tags=tags, **job_kwargs)

        # Map our simple interval string to schedule's syntax
        if interval == "minute":
            job = schedule_lib.every().minute
        elif interval == "hourly":
            job = schedule_lib.every().hour
        elif interval == "daily":
            job = schedule_lib.every().day
        elif interval == "weekly":
            job = schedule_lib.every().week
        else:
            raise ValueError(f"Unknown interval: {interval}")

        if at:
            job = job.at(at)

        # Register the job
        job.do(submit_to_worker)

        # Return original object so it can still be used directly
        return func

    return decorator
