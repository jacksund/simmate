# -*- coding: utf-8 -*-

import pickle

# from concurrent.futures import Executor # No need to inherit at the moment

from simmate.configuration import manage_django  # ensures setup
from simmate.workflows.core.execution.models import WorkItem
from simmate.workflows.core.execution.future import DjangoFuture

# This class is modeled after the following...
# https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py
# https://docs.python.org/3/library/concurrent.futures.html


class DjangoExecutor:  # (Executor)
    def __init__(self):
        """
        Sets up connection to the queue database. Unlike normal executors,
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
        pass

    def submit(self, fxn, /, *args, **kwargs):

        # The "/" in the input separates args into a tuple and kwargs into
        # a dictionary for me, which makes their storage very easy!

        # make the WorkItem where all of the provided inputs are pickled and
        # save the workitem to the database.
        # Pickling is just converting them to a byte string format
        # No lock is needed to do this because adding a new row is handled
        # by the database with ease, even if some different Executor is
        # adding another WorkItem at the same time.
        # TODO - should I put pickling in a "try" in case it fails?
        workitem = WorkItem.objects.create(
            fxn=pickle.dumps(fxn),
            args=pickle.dumps(args),
            kwargs=pickle.dumps(kwargs),
        )

        # create the future object
        future = DjangoFuture(pk=workitem.pk)

        # and return the future for use
        return future

    def map(self, fxn, iterables, timeout=None, chunksize=100):  # TODO
        # chunksize indicates how many to add at one
        # iterables is a list of (*args, **kwargs)
        # add many fn(*args, **kwargs) to queue

        # TODO -- This is not supported at the moment. I should use the
        # .bulk_create method to do this in the future:
        # https://docs.djangoproject.com/en/3.1/ref/models/querysets/#bulk-create

        # raise an error to ensure user sees this isn't supported yet.
        raise Exception('This method is not supported yet')

    def shutdown(self, wait=True, cancel_futures=False):  # TODO
        # whether to wait until the queue is empty
        # whether to cancel futures and clear database
        pass

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    # These methods are for managing and monitoring the queue
    # I attach these directly to the Executor rather than having a separate
    # DjangoQueue class that inherits from python's Queue module.
    # If there is a good reason to make a separate class in the future,
    # I can start from these methods here and the following link:
    # https://docs.python.org/3/library/queue.html

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

    def clear_queue(self, are_you_sure=False):
        """
        Empties the WorkItem database table and delete everything. This will
        not stop the workers if they are in the middle of a job though.
        """
        # Make sure the user ment to do this, otherwise raise an exception
        if not are_you_sure:
            raise Exception
        else:
            WorkItem.objects.all().delete()

    def clear_finished(self, are_you_sure=False):
        """
        Empties the WorkItem database table and delete everything. This will
        not stop the workers if they are in the middle of a job though.
        """
        # Make sure the user ment to do this, otherwise raise an exception
        if not are_you_sure:
            raise Exception
        else:
            WorkItem.objects.filter(status="F").delete()
