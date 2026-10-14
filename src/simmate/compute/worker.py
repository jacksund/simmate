# -*- coding: utf-8 -*-

import logging
import threading
import time
import traceback
from contextlib import ContextDecorator
from datetime import timedelta

import cloudpickle
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.utils import timezone
from rich import print

from simmate.database.core import DatabaseTable, table_column
from simmate.utils import get_class

from .utils import handle_sigterm
from .work_item import WorkerInterruptedError, WorkItem

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
        app_label = "compute_management"
        db_table = "compute__workers"

    # -------------------------------------------------------------------------

    active_statuses = ["Setting Up", "Idle", "Running"]
    status_options = [
        "Setting Up",
        "Idle",
        "Running",
        "Stopped",
        # for zombie workers determined by scheduler
        "Stale Heartbeat",
        "Crashed",
    ]
    status = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    """
    Current status of the worker
    """

    shutdown_flag = table_column.BooleanField(default=False)
    """
    Flag that when it is set to True, it will have the worker shut down at the
    next check-in/heartbeat. This is typically after a job completes
    """

    # last_heartbeat_at = table_column.DateTimeField(blank=True, null=True)
    # don't need because we just track the `updated_at` col with:
    #   self.save(update_fields=['updated_at'])

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

    # cached stats

    nitems_completed = table_column.IntegerField(blank=True, null=True)

    total_up_time = table_column.FloatField(blank=True, null=True)

    total_workflow_time = table_column.FloatField(blank=True, null=True)

    idle_percent = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------

    stale_after = timedelta(minutes=5)
    """
    An active worker that hasn't checked in for this long is considered stale
    (e.g. it was killed by SLURM, OOM, or a node failure).
    """

    crashed_after = timedelta(hours=1)
    """
    A worker that hasn't checked in for this long is considered crashed. Any
    WorkItems it was running are marked as INTERRUPTED.
    """

    # -------------------------------------------------------------------------

    def start(self):
        """
        Starts the worker process to begin working through WorkItems
        """

        # all within a try clause so that we can catch crtl+c shutdowns. SIGTERM
        # (e.g. from k8s or docker stopping the container) is treated the same.
        with handle_sigterm():
            try:
                self._run_loop()
            # if the user signals to stop with crtl+c (SIGINT = signal interrupt)
            # or the process is terminated (SIGTERM)
            except KeyboardInterrupt:
                logging.info("Stop signal recieved. Shutting down.")
                self._shutdown_on_interrupt()

    def _shutdown_on_interrupt(self):
        """
        Marks this worker as stopped and any WorkItem it was running as
        INTERRUPTED.
        """
        # we were stopped before the worker was even saved to the database
        if self.pk is None:
            return

        ninterrupted = WorkItem.objects.filter(status="R", worker=self).update(
            status="I",
            result_binary=cloudpickle.dumps(
                WorkerInterruptedError(
                    f"Worker {self.id} was stopped while running this item."
                )
            ),
            updated_at=timezone.now(),
        )
        if ninterrupted:
            logging.warning(
                "Shut down worker while WorkItem was still running. "
                "It has been marked as INTERRUPTED and can be requeued "
                "with `WorkItem.requeue_interrupted()`."
            )

        self.status = "Stopped"
        self.save(update_fields=["status", "updated_at"])

    def _run_loop(self):
        """
        The main loop of `start`, which runs until a stop condition is hit.
        """

        # separate vars so that we aren't saving 'inf' to database
        nitems_max = self.nitems_max if self.nitems_max else float("inf")
        timeout = self.timeout if self.timeout else float("inf")

        if not self.tags:
            self.tags = ["simmate"]

        # save worker entry to database
        self.status = "Setting Up"
        self.save()  # creates initial object

        # print the header in the console to let the user know the worker started
        print("[bold dark_cyan]" + HEADER_ART)

        logging.info(f"Starting worker with tags {list(self.tags)}")

        if self.startup_method:
            logging.info(f"Running startup method: '{self.startup_method}'")
            startup_method = get_class(self.startup_method)
            # keep our heartbeat alive in case of a long warmup
            with WorkerHeartbeat(worker_id=self.id):
                startup_method()

        # establish starting point for the worker
        time_start = time.time()
        self.nitems_completed = 0

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
                self.status = "Stopped"
                self.save(update_fields=["status", "updated_at"])
                return

            # check the number of jobs completed so far, and exit if we hit
            # the limit
            if self.nitems_completed >= nitems_max:
                logging.info(
                    f"Maximum number of WorkItems reached ({nitems_max}). "
                    "Shutting down."
                )
                self.status = "Stopped"
                self.save(update_fields=["status", "updated_at"])
                return

            # check if a shutdown was requested (e.g. from the web UI)
            if self.check_shutdown_flag():
                return

            # check the length of the queue and while it is empty, we want to
            # loop. The exception of looping endlessly is if we want the worker
            # to shutdown instead.
            while self.queue_size() == 0:

                # if it is empty, we want to sleep for a little and check again
                self.status = "Idle"
                self.save(update_fields=["status", "updated_at"])
                time.sleep(self.waittime_on_empty_queue)

                if self.check_shutdown_flag():
                    return

                # This is a special condition where we may want to close the
                # worker if the queue stays empty
                if self.close_on_empty_queue:
                    # after we just waited, let's check the queue size again
                    if self.queue_size() == 0:
                        # if it's still empty, we should close the worker
                        logging.info("The task queue is empty. Shutting down.")
                        self.status = "Stopped"
                        self.save(update_fields=["status", "updated_at"])
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

                # we now have a workitem to start
                self.status = "Running"
                self.save(update_fields=["status", "updated_at"])

                # update the status to running before starting it so no other
                # worker tries to grab the same WorkItem
                workitem.status = "R"
                workitem.worker = self
                workitem.started_at = timezone.now()
                workitem.save(
                    update_fields=["status", "worker", "started_at", "updated_at"]
                )

            # Print out the job ID that is being ran for the user to see
            logging.info(f"Running WorkItem with id {workitem.id}")

            # now let's unpickle the WorkItem components
            fxn = cloudpickle.loads(workitem.fxn)
            args = cloudpickle.loads(workitem.args)
            kwargs = cloudpickle.loads(workitem.kwargs)

            # Try running the WorkItem. A heartbeat thread keeps our
            # `updated_at` fresh so long jobs aren't mistaken for dead workers.
            try:
                with WorkerHeartbeat(worker_id=self.id):
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

                # will be saved to database instead of raised
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
            # status stays as running
            logging.info("Completed WorkItem")
            self.nitems_completed += 1
            self.save(update_fields=["nitems_completed", "updated_at"])

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

    def check_shutdown_flag(self) -> bool:
        """
        Reloads `shutdown_flag` from the database and, if it is set, marks this
        worker as stopped.

        Returns:
            True if the worker should shut down.
        """
        self.refresh_from_db(fields=["shutdown_flag"])
        if not self.shutdown_flag:
            return False
        logging.info("Shutdown was requested for this worker. Shutting down.")
        self.status = "Stopped"
        self.save(update_fields=["status", "updated_at"])
        return True

    # -------------------------------------------------------------------------

    @classmethod
    def get_active(cls):
        """
        Workers that are active and have checked in recently.
        """
        return cls.objects.filter(
            status__in=cls.active_statuses,
            updated_at__gte=timezone.now() - cls.stale_after,
        )

    @classmethod
    def get_stale(cls):
        """
        Workers that claim to be active but haven't checked in within
        `stale_after`. These have most likely been killed without a clean
        shutdown.
        """
        return cls.objects.filter(
            status__in=cls.active_statuses,
            updated_at__lt=timezone.now() - cls.stale_after,
        )

    @classmethod
    def update_stale_workers(cls) -> dict:
        """
        Updates the status of workers that have stopped checking in:

        - no check-in for `stale_after` (5 min) --> "Stale Heartbeat"
        - no check-in for `crashed_after` (1 hr) --> "Crashed", and any
          WorkItems they were running are marked as INTERRUPTED so they can be
          requeued with `WorkItem.requeue_interrupted()`.

        Note, `updated_at` is left untouched on workers so that it continues
        to reflect their last heartbeat.

        Returns:
            The number of workers marked as stale and crashed, as well as the
            number of WorkItems interrupted.
        """
        now = timezone.now()
        with transaction.atomic():
            # workers silent for over an hour are treated as dead
            crashed_ids = list(
                cls.objects.filter(
                    status__in=cls.active_statuses + ["Stale Heartbeat"],
                    updated_at__lt=now - cls.crashed_after,
                ).values_list("id", flat=True)
            )
            ninterrupted = WorkItem.objects.filter(
                status="R",
                worker_id__in=crashed_ids,
            ).update(
                status="I",
                result_binary=cloudpickle.dumps(
                    WorkerInterruptedError(
                        "Worker stopped sending heartbeats while running this "
                        "item and is presumed crashed."
                    )
                ),
                updated_at=now,
            )
            ncrashed = cls.objects.filter(id__in=crashed_ids).update(status="Crashed")
            nstale = cls.get_stale().update(status="Stale Heartbeat")

        if ncrashed or ninterrupted:
            logging.warning(
                f"Marked {ncrashed} worker(s) as crashed and {ninterrupted} "
                "WorkItem(s) as INTERRUPTED. These items can be requeued "
                "with `WorkItem.requeue_interrupted()`."
            )

        return {"stale": nstale, "crashed": ncrashed, "interrupted": ninterrupted}


class WorkerHeartbeat(ContextDecorator):
    """
    Runs a background thread that periodically bumps a worker's `updated_at`
    column while the main thread is busy running a WorkItem.

    Failures are logged but never raised, so a flaky database connection will
    not kill the WorkItem.
    """

    def __init__(self, worker_id: int, interval: float = 60):
        self.worker_id = worker_id
        self.interval = interval
        self.stop_signal = threading.Event()
        self.thread = None

    def _heartbeat_logic(self):
        try:
            while not self.stop_signal.wait(timeout=self.interval):
                try:
                    SimmateWorker.objects.filter(pk=self.worker_id).update(
                        updated_at=timezone.now()
                    )
                    # recover if we were marked stale (e.g. after a db blip)
                    SimmateWorker.objects.filter(
                        pk=self.worker_id,
                        status="Stale Heartbeat",
                    ).update(status="Running")
                except Exception as error:
                    logging.warning(f"Worker heartbeat failed: {error}")
        finally:
            # each thread gets its own db connection, so close it on exit
            connection.close()

    def __enter__(self):
        self.stop_signal.clear()
        self.thread = threading.Thread(
            target=self._heartbeat_logic,
            daemon=True,  # ensures thread exit when main thread errors
        )
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_signal.set()
        if self.thread:
            self.thread.join()
        return False
