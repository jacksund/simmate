# -*- coding: utf-8 -*-

import time

# import pickle
import cloudpickle  # needed to serialize Prefect workflow runs and tasks
from django.db import transaction

from simmate.database.base_data_types import DatabaseTable, table_column

# BUG: I have this database table within a module that calls "database.connect"
# at a higher level... Will this cause circular import issues?


class WorkItem(DatabaseTable):
    """
    A WorkItem is a future-like

    The name WorkItem comes from the naming convention use here:
    https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py

    There is a repo that goes one step further and makes a PickleField for django
    but this looks over the top for what I need -- even though django-picklefield
    is only one file! Still, I can use it as a reference if I ever run into bugs
    https://github.com/gintas/django-picklefield
    """

    class Meta:
        app_label = "engine"

    tags = table_column.JSONField(default=list)
    """
    List of tags to submit the task with, which helps with submitting workers
    for a specific type of task/workflow. (e.g. ["simmate", "custom"])
    """

    # These states were originally based on the python queue module, but we
    # updated them to match Prefect states that have more flexibility:
    # https://docs.prefect.io/concepts/states/
    class StatusOptions(table_column.TextChoices):
        PENDING = "P"
        RUNNING = "R"
        CANCELLED = "C"
        ERRORED = "E"
        FINISHED = "F"

    # TODO -- I should consider indexing this column for speed because it's
    # the most queried column by far.
    status = table_column.CharField(
        max_length=1,
        choices=StatusOptions.choices,
        default=StatusOptions.PENDING,
    )
    """
    the status/state of the workitem
    """

    command_not_found_failures = table_column.IntegerField(default=0)
    """
    Keeps track of the special-case "CommandNotFound" error that is hidden by
    workers. This keeps a tally of how many Workers that this task is triggering
    to shut down. This is important because it helps prevent total cluster
    shutdown from a single typo in a command. By default, workers will label
    a task as problematic if 2 workers give CommandNotFound errors.
    """

    # For serialization, I just use the pickle module, but in the future, I may
    # want to do a priority of MsgPk >> JSON >> Pickle. I could check if the given
    # object(s) has a serialize() method, check if has a to_json() method, and then
    # as a last resort just pickle the object.
    # https://docs.python.org/3/library/pickle.html
    #
    # Pickled objects are just written as byte strings, so I stored them in django
    # as a BinaryField which accepts bytes.
    # https://docs.djangoproject.com/en/3.1/ref/models/fields/#binaryfield

    fxn = table_column.BinaryField()
    """
    The function to be called, which is serialized into a binary format.
    """

    args = table_column.BinaryField(default=cloudpickle.dumps([]))
    """
    positional arguments to be passed into fxn
    """

    kwargs = table_column.BinaryField(default=cloudpickle.dumps({}))
    """
    keyword arguments to be passed into fxn
    """

    result_binary = table_column.BinaryField(blank=True, null=True)
    """
    the output of fxn(*args, **kwargs)
    """

    source = None
    """
    Source column is not needed so setting this to None disable the column
    """

    # TODO: Consider creating a separate table for Worker and linking it to this
    # table via a foreign key.
    # worker_id = table_column.CharField(max_length=50, blank=True, null=True)

    # -------------------------------------------------------------------------
    # The methods below turn this into a future-like object
    # These methods are based on:
    #   https://docs.python.org/3/library/concurrent.futures.html
    # Note in the methods below, that I make calls to WorkItem instead of self.
    # This is to ensure I can select_for_update() and also ensure I am
    # grabbing the most recent information.
    # -------------------------------------------------------------------------

    def cancel(self) -> bool:
        """
        Attempt to cancel the call. If the call is currently being executed or
        finished running and cannot be cancelled then the method will return
        False, otherwise the call will be cancelled and the method will return
        True.
        """

        # our lock exists only within this transation
        with transaction.atomic():
            # Query the WorkItem, lock it for editting, and check the status.
            workitem = WorkItem.objects.select_for_update().get(pk=self.pk)

            # check if the status is *not* PENDING
            if workitem.status != "P":
                # if so, the job is already running or finished, in which case
                # we can't cancel it.
                return False

            else:
                # If it is still pending, we can go ahead and cancel it.
                # This does not delete the task from the queue database though
                workitem.status = "C"
                workitem.save()
                return True

    def is_pending(self) -> bool:
        """
        Return True if the call is still pending.
        """
        # I don't use a lock to check the status here
        workitem = WorkItem.objects.only("status").get(pk=self.pk)

        # check the status and indicate whether it is CANCELED or not
        if workitem.status == "P":
            return True
        else:
            return False

    def is_cancelled(self) -> bool:
        """
        Return True if the call was successfully cancelled.
        """
        # I don't use a lock to check the status here
        workitem = WorkItem.objects.only("status").get(pk=self.pk)

        # check the status and indicate whether it is CANCELED or not
        if workitem.status == "C":
            return True
        else:
            return False

    def is_running(self) -> bool:
        """
        Return True if the call is currently being executed and cannot be cancelled.
        """
        # I don't use a lock to check the status here
        workitem = WorkItem.objects.only("status").get(pk=self.pk)

        # check the status and indicate whether it is RUNNING or not
        if workitem.status == "R":
            return True
        else:
            return False

    def is_done(self) -> bool:
        """
        Return True if the call was successfully cancelled or finished running.
        """
        # I don't use a lock to check the status here
        workitem = WorkItem.objects.only("status").get(pk=self.pk)

        # check the status and indicate whether it is FINISHED or CANCELED
        if workitem.status == "F" or workitem.status == "C":
            return True
        else:
            return False

    def result(
        self,
        timeout: float = None,
        sleep_step: float = 5,
        raise_error: bool = True,
    ) -> any:
        """
        Return the value returned by the call. If the call hasn’t yet completed
        then this method will wait up to timeout seconds. If the call hasn’t
        completed in timeout seconds, then a concurrent.futures.TimeoutError
        will be raised. timeout can be an int or float. If timeout is not
        specified or None, there is no limit to the wait time.

        If the future is cancelled before completing then CancelledError
        will be raised.

        If the call raised, this method will raise the same exception.
        """
        # if no timeout was set, use infinity so we wait forever.
        if not timeout:
            timeout = float("inf")

        # Loop endlessly until the job completes or we timeout
        time_start = time.time()

        while (time.time() - time_start) < timeout:
            # I don't use a lock to check the status here
            workitem = WorkItem.objects.only("status", "result_binary").get(pk=self.pk)
            status = workitem.status

            if status == "F" or status == "E":  # FINISHED or ERRORED
                # grab the result, unpickle it, and return it
                result = cloudpickle.loads(workitem.result_binary)
                # if the result is an Error or Exception, raise it
                if isinstance(result, Exception) and raise_error:
                    raise result
                # otherwise return the result as-is
                else:
                    return result

            elif status == "C":  # CANCELED
                raise CancelledError(
                    "This item was cancelled and has no result. If this is unexpected, "
                    "be sure to check your worker logs. Misconfiguration or a `command "
                    "not found` error can be the cause of your job getting cancelled."
                )

            elif status == "P" or status == "R":  # PENDING or RUNNING
                # sleep the set amount before restarting the while loop
                time.sleep(sleep_step)

        # if the loop exits and we reached this line, then we've hit the timeout
        raise TimeoutError("The time-limit to wait for this result has been exceeded")


class CancelledError(Exception):
    pass
