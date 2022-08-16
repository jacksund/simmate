# -*- coding: utf-8 -*-

import logging
import time
import traceback

import cloudpickle  # needed to serialize Prefect workflow runs and tasks
from django.db import transaction

from simmate.workflow_engine.execution.database import WorkItem

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
    """
    The default worker that connect to Simmate database for workflows submitted
    via the `run_cloud` method.
    """

    # Ideally, this worker would involve multiple threads threads going. One
    # thread would update the queue database with a "heartbeat" to let it know
    # that it is still working on tasks. The other thread will run the given
    # workitems in serial. I could even allow for more threads so that this
    # worker can run multiple workitems at once and in parallel.
    # However, if this level of implementation is needed, we should instead
    # switch to using Prefect, which has it built in.

    # Consider making this a database object so that we can track workers in
    # the UI and know how many are running.

    def __init__(
        self,
        # limit of tasks and lifetime of the worker
        nitems_max: int = None,
        timeout: float = None,
        # wait_on_timeout=False, # TODO
        # settings on what to do when the queue is empty
        close_on_empty_queue: bool = False,
        waittime_on_empty_queue: float = 1,
        tags: list[str] = ["simmate"],  # should default be empty...?
    ):
        """
        Configures a worker that connects to the default executor backend.
        By default the worker will run endlessly.

        #### Parameters:

        - `nitems_max`:
            The maximum number of workitems to run before closing down
            if no limit was set, we can go to infinity.

        - `timeout`:
            Don't start a new workitem after this time. The worker will be shut down.
            if no timeout was set, use infinity so we wait forever.

        - `close_on_empty_queue`:
            whether to close if the queue is empty

        - `waittime_on_empty_queue`:
            if the queue is found to be empty, check the queue again after
            this time sleeping.

        - `tags`:
            the tags to query tasks for. If no tags were given, the worker will
            query for tasks that have NO tags

        """
        self.tags = tags
        self.nitems_max = nitems_max or float("inf")
        self.timeout = timeout or float("inf")
        self.close_on_empty_queue = close_on_empty_queue
        self.waittime_on_empty_queue = waittime_on_empty_queue

        # whether to wait on the running workitems to finish before shutting down
        # the timedout worker.
        # self.wait_on_timeout = wait_on_timeout # # TODO

    def start(self):
        """
        Starts the worker process to begin working through WorkItems
        """

        # print the header in the console to let the user know the worker started
        logging.info("\n" + HEADER_ART)

        # loggin helpful info
        logging.info(f"Starting worker with tags {list(self.tags)}")

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
                logging.info(
                    "The time-limit for this worker has been hit. Shutting down."
                )
                return

            # check the number of jobs completed so far, and exit if we hit
            # the limit
            if ntasks_finished >= self.nitems_max:
                logging.info(
                    f"Maximum number of WorkItems reached ({self.nitems_max}). "
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

            # If we've made it this far, we're ready to grab a new WorkItem
            # and run it!
            # Query for PENDING WorkItems, lock it for editting, and update
            # the status to RUNNING. And grab the first result
            workitem = (
                WorkItem.objects.select_for_update()
                .filter(status="P")
                .filter_by_tags(self.tags)
                .first()
            )

            # our lock exists only within this transation
            with transaction.atomic():
                # update the status to running before starting it so no other
                # worker tries to grab the same WorkItem
                workitem.status = "R"
                # TODO -- indicate that the WorkItem is with this Worker (relationship)
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
                from simmate.workflow_engine.s3_workflow import CommandNotFoundError

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
                            workitem.status = "P"
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
            tags=["simmate"],
        )
        worker.start()
