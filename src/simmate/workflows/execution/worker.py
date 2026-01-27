# -*- coding: utf-8 -*-

import logging
import time
import traceback

import cloudpickle
from django.contrib.auth.models import User
from django.db import transaction
from rich import print

from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.utilities import get_class

from .work_item import WorkItem

# This string is just something fancy to display in the console when a worker
# starts up.
# This uses "Small Slant" from https://patorjk.com/software/taag/
HEADER_ART = r"""
=====================================================================
   _____                  __        _      __         __
  / __(_)_ _  __ _  ___ _/ /____   | | /| / /__  ____/ /_____ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_)  | |/ |/ / _ \/ __/  '_/ -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/   |__/|__/\___/_/ /_/\_\\__/_/

=====================================================================
"""


class SimmateWorker(DatabaseTable):
    """
    The default worker that connect to Simmate database for workflows submitted
    via the `run_cloud` method.
    """

    class Meta:
        app_label = "workflows"
        db_table = "workflow_engine__workers"

    # -------------------------------------------------------------------------

    html_display_name = "Workers"
    html_description_short = (
        "Workers are individual compute resources that pick up and run "
        "items that have been submitted to the queue."
    )

    # -------------------------------------------------------------------------

    status_options = [
        "Setting Up",
        "Running",
        "Stale Heartbeat",
        "Crashed",  # for zombie workers determined by scheduler
        "Stopped",
    ]
    status = table_column.CharField(
        max_length=10,
        blank=True,
        null=True,
    )
    """
    Current status of the worker
    """

    last_heartbeat_at = table_column.DateTimeField(blank=True, null=True)

    shutdown_flag = table_column.BooleanField(default=False)
    """
    Flag that when it is set to True, it will have the worker shut down at the
    next check-in/heartbeat. This is typically after a job completes
    """

    # -------------------------------------------------------------------------

    # total_up_time

    # total_cpu_time

    # up_time_efficiency

    # total_jobs

    # -------------------------------------------------------------------------

    owner = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        related_name="workers",
        blank=True,
        null=True,
    )

    ncores = table_column.FloatField(blank=True, null=True)

    ram = table_column.FloatField(blank=True, null=True)

    computer_system = table_column.CharField(
        max_length=75,
        blank=True,
        null=True,
    )

    directory = table_column.CharField(
        max_length=250,
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    # kwargs used to start the worker

    # limit of tasks and lifetime of the worker
    tags = table_column.JSONField(default=list)
    """
    the tags to query tasks for. If no tags were given, the worker will
    query for tasks that have NO tags
    """

    nitems_max = table_column.IntegerField(blank=True, null=True)
    """
    The maximum number of workitems to run before closing down
    if no limit was set, we can go to infinity.
    """

    timeout = table_column.FloatField(blank=True, null=True)
    """
    Don't start a new workitem after this time. The worker will be shut down.
    if no timeout was set, use infinity so we wait forever.
    """

    # settings on what to do when the queue is empty
    close_on_empty_queue = table_column.BooleanField(default=False)
    """
    whether to close if the queue is empty
    """

    waittime_on_empty_queue = table_column.FloatField(default=15)
    """
    if the queue is found to be empty, check the queue again after
    this time sleeping
    """

    startup_method = table_column.TextField(blank=True, null=True)
    """
    The python path to a method that should be called before running any items.
    This is typically only used for specialized workers that need a cache-warmup
    """

    # -------------------------------------------------------------------------

    def start(self):
        """
        Starts the worker process to begin working through WorkItems
        """

        # separate vars so that we aren't saving 'inf' to database
        nitems_max = self.nitems_max if self.nitems_max else float("inf")
        timeout = self.timeout if self.timeout else float("inf")

        if not self.tags:
            self.tags = ["simmate"]

        # save worker entry to database
        self.status = "Running"
        self.save()

        # print the header in the console to let the user know the worker started
        print("[bold dark_cyan]" + HEADER_ART)

        logging.info(f"Starting worker with tags {list(self.tags)}")

        if self.startup_method:
            logging.info(f"Running startup method: '{self.startup_method}'")
            startup_method = get_class(self.startup_method)
            startup_method()

        # establish starting point for the worker
        time_start = time.time()
        ntasks_finished = 0

        logging.info("Worker is ready & listening for WorkItems")
        # Loop endlessly until one of the following happens...
        #   the timeout limit is hit
        #   the queue is empty
        #   the nitems limit is hit
        while True:
            # check for timeout before starting a new workitem and exit
            # if we've hit the limit.
            if (time.time() - time_start) > timeout:
                logging.info(
                    "The time-limit for this worker has been hit. Shutting down."
                )
                return

            # check the number of jobs completed so far, and exit if we hit
            # the limit
            if ntasks_finished >= nitems_max:
                logging.info(
                    f"Maximum number of WorkItems reached ({nitems_max}). "
                    "Shutting down."
                )
                return

            # check the length of the queue and while it is empty, we want to
            # loop. The exception of looping endlessly is if we want the worker
            # to shutdown instead.
            while self.queue_size() == 0:
                # if it is empty, we want to sleep for a little and check again
                time.sleep(self.waittime_on_empty_queue)

                # This is a special condition where we may want to close the
                # worker if the queue stays empty
                if self.close_on_empty_queue:
                    # after we just waited, let's check the queue size again
                    if self.queue_size() == 0:
                        # if it's still empty, we should close the worker
                        logging.info("The task queue is empty. Shutting down.")
                        return

            # make this atomic so that multiple workers don't accidentally
            # grab the same job.
            with transaction.atomic():
                # If we've made it this far, we're ready to grab a new WorkItem
                # and run it!
                # Query for PENDING WorkItems, lock it for editting, and update
                # the status to RUNNING. And grab the first result
                workitem = (
                    WorkItem.objects.select_for_update(skip_locked=True)
                    .filter(status="P")
                    .filter_by_tags(self.tags)
                    .order_by("created_at")
                    .first()
                )

                # Catch race condition where no workitems are available any more.
                # If this is the case, we just restart the while loop.
                if not workitem:
                    continue

                # update the status to running before starting it so no other
                # worker tries to grab the same WorkItem
                workitem.status = "R"
                workitem.worker = self
                workitem.save()

            # Print out the job ID that is being ran for the user to see
            logging.info(f"Running WorkItem with id {workitem.id}")

            # now let's unpickle the WorkItem components
            fxn = cloudpickle.loads(workitem.fxn)
            args = cloudpickle.loads(workitem.args)
            kwargs = cloudpickle.loads(workitem.kwargs)

            # Try running the WorkItem
            try:
                result = fxn(*args, **kwargs)
            # if it fails, we want to "capture" the error and return it
            # rather than have the Worker fail itself.
            except Exception as exception:
                traceback.print_exc()

                logging.warning(
                    "Task failed with the error shown above. \n\n"
                    "If you are unfamilar with error tracebacks and find this error "
                    "difficult to read, you can learn more about these errors "
                    "here:\n https://realpython.com/python-traceback/\n\n"
                    "Please open a new issue on our github page if you believe "
                    "this is a bug:\n https://github.com/jacksund/simmate/issues/\n\n"
                )

                # local import to prevent circular import issues
                from simmate.workflows.base_flow_types.s3 import CommandNotFoundError

                # The most common error (by far) is a command-not-found issue.
                # We want to handle this separately -- whereas other exceptions
                # we just pass on to the results.
                if isinstance(exception, CommandNotFoundError):
                    logging.warning(
                        "This WorkItem failed with a 'command not found' error. "
                        "This worker is likely improperly configured or "
                        "you have a typo in your command."
                    )

                    with transaction.atomic():
                        nfailures = workitem.command_not_found_failures + 1

                        # Check if this task is problematic. If this error happened
                        # with another worker, we likely have a problematic task
                        if nfailures == 2:
                            logging.warning(
                                "This is the 2nd occurance with this task causing "
                                "a 'command not found' problem. In case this a typo "
                                "in your command, we are marking the task as CANCELLED "
                                "to prevent it from shutting down other workers."
                            )
                            workitem.status = "C"
                            workitem.save()
                            # the result will be set below

                        # Otherwise the user likely just forgot to use module load
                        else:
                            logging.info(
                                f"Resetting WorkItem {workitem.id} to 'Pending' so "
                                "another worker can retry."
                            )

                            workitem.command_not_found_failures = nfailures
                            workitem.status = "P"  # marked as PENDING to retry
                            workitem.save()
                    logging.info("Shutting down to prevent repeated issues.")
                    return

                result = exception

            # whatever the result, we need to try to pickle it now
            try:
                result_pickled = cloudpickle.dumps(result)
            # if this fails, we even want to pickle the error and return it
            except Exception as exception:
                # otherwise package the full error
                result_pickled = cloudpickle.dumps(exception)

            # our lock exists only within this transation
            with transaction.atomic():
                # requery the WorkItem to restart our lock
                workitem = WorkItem.objects.select_for_update().get(pk=workitem.pk)

                # pickle the result and update the workitem's result and status
                # !!! should I have the pickle inside of a Try?
                workitem.result_binary = result_pickled
                # mark as finished or errored depending on result value
                workitem.status = "E" if isinstance(result, Exception) else "F"
                workitem.save()

            # mark down that we've completed one WorkItem
            ntasks_finished += 1

            # Print out the job ID that was just finished for the user to see.
            logging.info("Completed WorkItem")

    def queue_size(self) -> int:
        """
        Return the approximate size of the queue.
        """
        # Count the number of WorkItem(s) that have a status of PENDING
        # !!! Should I include RUNNING in the count? If so I do that with...
        #   from django.db.models import Q
        #   ...filter(Q(status="P") | Q(status="R"))
        queue_size = (
            WorkItem.objects.filter(status="P").filter_by_tags(self.tags).count()
        )
        return queue_size

    @classmethod
    def run_singleflow_worker(cls):
        """
        A convenience method for running a worker that...
        1. shuts down immediately if the queue is empty
        2. shuts down after a single workflow run

        Because this type of worker is frequently used for HPC clusters, we
        make a convenience method for it.
        """
        worker = cls(
            nitems_max=1,
            close_on_empty_queue=True,
            waittime_on_empty_queue=5,
            tags=["simmate"],
        )
        worker.start()


# -----------------------------------------------------------------------------

# Typically workers have a heartbeat thread that can separately check in with
# the database so that users can see it is still up and running. However,
# this introduces context switching and other complexities that I would like
# to avoid with DFT programs on HPC. It's much cleaner to have a single python
# thread. If time tests show heartbeat threads are a non-issue, I can use
# a decorator like this:
#
# import threading
# from contextlib import ContextDecorator
#
# class worker_heartbeat(ContextDecorator):
#     # then add to method with...     @worker_heartbeat(interval=300)
#
#     def __init__(self, interval=5):
#         self.interval = interval
#         self.stop_signal = threading.Event()
#         self.thread = None
#
#     def _heartbeat_logic(self):
#         while not self.stop_signal.is_set():
#             logging.info("heartbeat is active")  # or ping database
#             self.stop_signal.wait(timeout=self.interval)
#
#     def __enter__(self):
#         self.stop_signal.clear()
#         self.thread = threading.Thread(
#             target=self._heartbeat_logic,
#             daemon=True,  # ensures thread exit when main thread errors
#         )
#         self.thread.start()
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.stop_signal.set()
#         if self.thread:
#             self.thread.join()
#         logging.info("heartbeat stopped")
