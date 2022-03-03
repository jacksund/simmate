# -*- coding: utf-8 -*-

import time

# import pickle
import cloudpickle  # needed to serialize Prefect workflow runs and tasks

from django.db import transaction

from simmate.workflow_engine.execution.database import WorkItem

# In the future, I might want this worker to be a local dask cluster that has
# two threads going. One thread will update the queue database with a "heartbeat" to
# let it know that it is still working on tasks. The other thread will run the
# given workitems in serial. I could even allow for more threads so that this
# worker can run multiple workitems at once and in parallel. I'm not sure if
# asyncio would play into this though.

# This string is just something fancy to display in the console when a worker
# starts up.
# This uses "Small Slant" from https://patorjk.com/software/taag/
HEADER_ART = r"""
   _____                  __        _      __         __
  / __(_)_ _  __ _  ___ _/ /____   | | /| / /__  ____/ /_____ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_)  | |/ |/ / _ \/ __/  '_/ -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/   |__/|__/\___/_/ /_/\_\\__/_/

"""


class SimmateWorker:
    def __init__(
        self,
        # limit of tasks and lifetime of the worker
        nitems_max=None,
        timeout=None,
        # wait_on_timeout=False, # TODO
        # settings on what to do when the queue is empty
        close_on_empty_queue=False,
        waittime_on_empty_queue=60,
    ):

        # the maximum number of workitems to run before closing down
        # if no limit was set, we can go to infinity!
        self.nitems_max = nitems_max or float("inf")

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
        self.waittime_on_empty_queue = waittime_on_empty_queue

    def start(self):

        # print the header in the console to let the user know the worker started
        print(HEADER_ART)

        # establish starting point for the worker
        time_start = time.time()
        ntasks_finished = 0

        # Loop endlessly until one of the following happens...
        #   the timeout limit is hit
        #   the queue is empty
        #   the nitems limit is hit
        while True:

            # check for timeout before starting a new workitem and exit
            # if we've hit the limit.
            if (time.time() - time_start) > self.timeout:
                # TODO - check wait_on_timeout if running in parallel.
                print("The time-limit for this worker has been hit.")
                return

            # check the number of jobs completed so far, and exit if we hit
            # the limit
            if ntasks_finished >= self.nitems_max:
                print("Maxium number of WorkItems hit for this worker.")
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
                        print("The queue is empty so the worker has been closed.")
                        return

            # If we've made it this far, we're ready to grab a new WorkItem
            # and run it!
            # Query for PENDING WorkItems, lock it for editting, and update
            # the status to RUNNING
            workitem = WorkItem.objects.select_for_update().filter(status="P").first()

            # our lock exists only within this transation
            with transaction.atomic():
                # update the status to running before starting it so no other
                # worker tries to grab the same WorkItem
                workitem.status = "R"
                # TODO -- indicate that the WorkItem is with this Worker (relationship)
                workitem.save()

            # Print out the job ID that is being ran for the user to see
            print(f"Running WorkItem with id {workitem.id}.")

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
                result = exception

            # whatever the result, we need to try to pickle it now
            try:
                result_pickled = cloudpickle.dumps(result)
            # if this fails, we even want to pickle the error and return it
            except Exception as exception:
                result_pickled = cloudpickle.dumps(exception)

            # requery the WorkItem to restart our lock
            workitem = WorkItem.objects.select_for_update().get(pk=workitem.pk)

            # our lock exists only within this transation
            with transaction.atomic():
                # pickle the result and update the workitem's result and status
                # !!! should I have the pickle inside of a Try?
                workitem.result = result_pickled
                workitem.status = "F"
                workitem.save()

            # mark down that we've completed one WorkItem
            ntasks_finished += 1

            # Print out the job ID that was just finished for the user to see.
            print("Completed WorkItem.")

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
