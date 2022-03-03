# -*- coding: utf-8 -*-

import time

# import pickle
import cloudpickle  # needed to serialize Prefect workflow runs and tasks

# from concurrent.futures import Future # No need to inherit at the moment

from simmate.workflow_engine.execution.database import WorkItem

# class based on...
# https://docs.python.org/3/library/concurrent.futures.html
# Some methods still need to be added, but I have no need for them yet.

# locking rows is done by...
# https://docs.djangoproject.com/en/3.1/ref/models/querysets/#select-for-update


class DjangoFuture:  # (Future)
    def __init__(self, pk):

        # This is the WorkItem personal key which tells us which row in the table
        # we should loook at.
        self.pk = pk

    def cancel(self):
        """
        Attempt to cancel the call. If the call is currently being executed or
        finished running and cannot be cancelled then the method will return
        False, otherwise the call will be cancelled and the method will return
        True.
        """
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

    def cancelled(self):
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

    def running(self):
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

    def done(self):
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

    def result(self, timeout=None, sleep_step=0.1):
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
            workitem = WorkItem.objects.only("status", "result").get(pk=self.pk)
            status = workitem.status

            if status == "F":  # FINISHED
                # grab the result, unpickle it, and return it
                result = cloudpickle.loads(workitem.result)
                # if the result is an Error or Exception, raise it
                if isinstance(result, Exception):
                    raise result
                # otherwise return the result as-s
                else:
                    return result

            elif status == "C":  # CANCELED
                raise CancelledError("This item was cancelled and has no result")

            elif status == "P" or status == "R":  # PENDING or RUNNING
                # sleep the set amount before restarting the while loop
                time.sleep(sleep_step)

        # if the loop exits and we reached this line, then we've hit the timeout
        raise TimeoutError("The time-limit to wait for this result has been exceeded")


class CancelledError(Exception):
    pass
