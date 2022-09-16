# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

import cloudpickle  # needed to serialize Prefect workflow runs and tasks
from django.utils import timezone
from rich import print

from simmate.workflow_engine.execution.database import WorkItem


class SimmateExecutor:
    """
    Sets up a connection to the queue database. Unlike normal executors,
    this does not set up any workers -- you must launch Worker instances
    elsewhere. It's primary role is to connect to the queue database
    and generate futures for workers. Therefore, think of the Executor
    as how you SUBMIT tasks and then the Worker is how you RUN jobs. You
    need both classes to have the setup working properly.

    Only use this Executor when Dask can't solve your problem! It's main
    use it to bypass university HPC cluster's firewalls because here worker
    signals are one-directional -- that is they query a database and there
    is never a signal sent to the worker like other executors do. Thus
    we can have workers anywhere we'd like as long as they have access
    to internet - so even multiple HPC clusters will work. At the moment,
    the executor has no idea how many workers exist and their state. I may
    add a "worker heartbeat" table to the queue database for the executor
    to read and run managerial tasks based off though.
    """

    # This class is modeled after the following...
    # https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py
    # https://docs.python.org/3/library/concurrent.futures.html
    # from concurrent.futures import Executor # No need to inherit at the moment

    @staticmethod
    def submit(
        fxn: callable,
        *args,
        tags: list[str] = [],
        **kwargs,
    ) -> WorkItem:

        # The *args and **kwargs input separates args into a tuple and kwargs into
        # a dictionary for me, which makes their storage very easy!

        # make the WorkItem where all of the provided inputs are pickled and
        # save the workitem to the database.
        # Pickling is just converting them to a byte string format
        # No lock is needed to do this because adding a new row is handled
        # by the database with ease, even if some different Executor is
        # adding another WorkItem at the same time.
        # TODO - should I put pickling in a "try" in case it fails?
        workitem = WorkItem.objects.create(
            fxn=cloudpickle.dumps(fxn),
            args=cloudpickle.dumps(args),
            kwargs=cloudpickle.dumps(kwargs),
            tags=tags,  # should be json serializable already
        )

        # and return the workitem/future for use
        return workitem

    @staticmethod
    def wait(workitems: list[WorkItem]):
        """
        Waits for all futures to complete before returning a list of their results
        """
        # If a dictionary of {key1: future1, key2: future2, ...} is given,
        # then we return a dictionary of which futures replaced by results.
        # NOTE: this is really for compatibility with Prefect's FlowRunner.
        if isinstance(workitems, dict):
            logging.info("waiting for workflows to finish")
            import time

            time.sleep(10)
            for key, workitem in workitems.items():
                print((key, workitem, workitem.pk, workitem.done()))
                # print(future.result())
            return {key: workitem.result() for key, workitem in workitems.items()}
        # otherwise this is a list of futures, so return a list of results
        else:
            return [workitem.result() for workitem in workitems]

    # -------------------------------------------------------------------------
    # These methods are for managing and monitoring the queue
    # I attach these directly to the Executor rather than having a separate
    # DjangoQueue class that inherits from python's Queue module.
    # If there is a good reason to make a separate class in the future,
    # I can start from these methods here and the following link:
    # https://docs.python.org/3/library/queue.html
    # -------------------------------------------------------------------------

    @staticmethod
    def queue_size() -> int:
        """
        Return the approximate size of the queue.
        """
        # Count the number of WorkItem(s) that have a status of PENDING
        # !!! Should I include RUNNING in the count? If so I do that with...
        #   from django.db.models import Q
        #   ...filter(Q(status="P") | Q(status="R"))
        queue_size = WorkItem.objects.filter(status="P").count()
        return queue_size

    @staticmethod
    def delete_all(confirm: bool = False):
        """
        Empties the WorkItem database table and delete everything. This will
        not stop the workers if they are in the middle of a job though.
        """
        # Make sure the user ment to do this, otherwise raise an exception
        if not confirm:
            raise Exception(
                "Are you sure you want to do this? This deletes all of your queue "
                "data and you can't get it back. If so, run this method again "
                "with confirmation."
            )
        else:
            WorkItem.objects.all().delete()

    @staticmethod
    def delete_finished(confirm: bool = False):
        """
        Empties the WorkItem database table and delete everything. This will
        not stop the workers if they are in the middle of a job though.
        """
        # Make sure the user ment to do this, otherwise raise an exception
        if not confirm:
            raise Exception(
                "Are you sure you want to do this? This deletes finished "
                "entries from your queue-table and you can't get them back. "
                "If so, run this method again with confirmation."
            )
        else:
            WorkItem.objects.filter(status="F").delete()

    @staticmethod
    def show_error_summary():

        errored_jobs = WorkItem.objects.filter(status="E").all()

        if not errored_jobs:
            print("No errored jobs found. Everything looks good.")
            return

        print("ID | ERROR")

        for job in errored_jobs:
            try:
                job.result()
            except Exception as error:
                print(f"{job.id} | {error}")

    @staticmethod
    def show_stats() -> int:
        npending = WorkItem.objects.filter(status="P").count()
        nrunning = WorkItem.objects.filter(status="R").count()
        ncanceled = WorkItem.objects.filter(status="C").count()
        nfinished = WorkItem.objects.filter(status="F").count()
        nerrored = WorkItem.objects.filter(status="E").count()

        if nfinished:
            error_percent = (nerrored / (nerrored + nfinished)) * 100
        else:
            error_percent = 0

        nrunning_long = WorkItem.objects.filter(
            status="R",
            updated_at__lte=timezone.now() - timedelta(days=1),
        ).count()

        print(f"PENDING:   {npending}")
        print(f"RUNNING:   {nrunning} ({nrunning_long} for +24hrs)")
        print(f"FINISHED:  {nfinished}")
        print(f"ERRORED:   {nerrored} ({error_percent:.2f}%)")
        print(f"CANCELED:  {ncanceled}")

    # -------------------------------------------------------------------------
    # Extra methods to add if I want to be consistent with other Executor classes
    # -------------------------------------------------------------------------

    # @staticmethod
    # def map(fxn, iterables, timeout=None, chunksize=100):  # TODO
    #     # chunksize indicates how many to add at one
    #     # iterables is a list of (*args, **kwargs)
    #     # add many fn(*args, **kwargs) to queue

    #     # TODO -- This is not supported at the moment. I should use the
    #     # .bulk_create method to do this in the future:
    #     # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#bulk-create

    #     # raise an error to ensure user sees this isn't supported yet.
    #     raise Exception("This method is not supported yet")

    # @staticmethod
    # def shutdown(wait=True, cancel_futures=False):  # TODO
    #     # whether to wait until the queue is empty
    #     # whether to cancel futures and clear database
    #     pass
