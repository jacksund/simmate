# -*- coding: utf-8 -*-

import pickle
import time

from django.db import transaction

from simmate.configuration import manage_django  # ensures setup
from simmate.workflows.core.execution.models import WorkItem

# In the future, I might want this worker to be a local dask cluster that has
# two threads going. One thread will update the queue database with a "heartbeat" to
# let it know that it is still working on tasks. The other thread will run the
# given workitems in serial. I could even allow for more threads so that this
# worker can run multiple workitems at once and in parallel. I'm not sure if
# asyncio would play into this though.


class DjangoWorker:
    def __init__(
        self,
        # limit of tasks and lifetime of the worker
        nitems_before_closing=None,
        timeout=None,
        # wait_on_timeout=False, # TODO
        # settings on what to do when the queue is empty
        close_on_empty_queue=False,
        close_wait=60,
    ):

        # the maximum number of workitems to run before closing down
        # if no limit was set, we can go to infinity!
        self.nitems_before_closing = nitems_before_closing or float("inf")

        # Don't start a new workitem after this time. The worker will be shut down.
        # if no timeout was set, use infinity so we wait forever.
        self.timeout = timeout or float("inf")

        # whether to wait on the running workitems to finish before shutting down
        # the timedout worker.
        # self.wait_on_timeout = wait_on_timeout # # TODO

        # whether to close if the queue is empty
        self.close_on_empty_queue = close_on_empty_queue
        # if the queue is found to be empty, we will give it one last chance
        # to fill. Check the queue again after this time sleeping and if it is
        # still empty, close the worker.
        self.close_wait = close_wait

    def start(self):

        # establish starting point for the worker
        time_start = time.time()
        ntasks_finished = 0

        # Loop endlessly until one of the following happens...
        #   the timeout limit is hit
        #   the queue is empty
        #   the nitems limit is hit
        while True:

            # check for timeout before starting a new workitem
            if (time.time() - time_start) < self.timeout:
                # TODO - check wait_on_timeout if running in parallel.
                raise TimeoutError("The time-limit for this worker has been hit")

            # check the number of jobs completed so far
            if ntasks_finished > self.nitems_before_closing:
                raise MaxWorkItemsError(
                    "Maxium number of WorkItems hit for this worker"
                )

            # if we close on empty queues, we should check the queue size
            if self.close_on_empty_queue:
                # check the length of the queue
                if self.queue_size() == 0:
                    # if it is empty, we want to sleep for a little and check again
                    time.sleep(self.close_wait)
                    if self.queue_size() == 0:
                        # if it's still empty, we should close the worker
                        raise EmptyQueueError(
                            "The queue is empty so the worker has been closed"
                        )

            # If we've made it this far, we're ready to grab a new WorkItem
            # and run it!
            # Query for PENDING WorkItems, lock it for editting, and update
            # the status to RUNNING
            workitem = WorkItem.objects.select_for_update().first(status="P")

            # our lock exists only within this transation
            with transaction.atomic():
                # update the status to running before starting it so no other
                # worker tries to grab the same WorkItem
                workitem.status = "R"
                # TODO -- indicate that the WorkItem is with this Worker (relationship)
                workitem.save()

            # now let's unpickle the WorkItem components
            fxn = pickle.loads(workitem.fxn)
            args = pickle.loads(workitem.args)
            kwargs = pickle.loads(workitem.kwargs)

            # Try running the WorkItem
            try:
                result = fxn(*args, **kwargs)
            # if it fails, we want to "capture" the error and return it
            # rather than have the Worker fail itself.
            except Exception as exception:
                result = exception

            # whatever the result, we need to try to pickle it now
            try:
                result_pickled = pickle.dumps(result)
            # if this fails, we even want to pickle the error and return it
            except Exception as exception:
                result_pickled = pickle.dumps(exception)

            # requery the WorkItem to restart our lock
            workitem = WorkItem.objects.select_for_update().get(pk=workitem.pk)

            # our lock exists only within this transation
            with transaction.atomic():
                # pickle the result and update the workitem's result and status
                # !!! should I have the pickle inside of a Try?
                workitem.result = result_pickled
                workitem.status = "F"
                workitem.save()

        # if the loop exits and we reached this line, then we've hit the timeout

    def queue_size(self):
        """
        Return the approximate size of the queue.
        """
        # Count the number of WorkItem(s) that have a status of PENDING
        # !!! Should I include RUNNING in the count? If so I do that with...
        #   from django.db.models import Q
        #   ...filter(Q(status="P") | Q(status="R"))
        queue_size = WorkItem.objects.filter(status="P").count()
        return queue_size


class MaxWorkItemsError(Exception):
    pass


class EmptyQueueError(Exception):
    pass
