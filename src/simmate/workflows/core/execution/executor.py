# -*- coding: utf-8 -*-

from concurrent.futures import Executor

# This class is modeled after the following...
# https://github.com/python/cpython/blob/master/Lib/concurrent/futures/thread.py
# https://docs.python.org/3/library/concurrent.futures.html


class DjangoExecutor(Executor):
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
        # connect to db
        pass

    def submit(self, fn, *args, **kwargs):
        # with a lock
        # add fn(*args, **kwargs) to queue
        pass

    def map(self, func, iterables, timeout=None, chunksize=100):
        # chunksize indicates how many to add at one
        # iterables is a list of (*args, **kwargs)
        # with a lock
        # add many fn(*args, **kwargs) to queue
        pass

    def shutdown(self, wait=True, cancel_futures=False):
        # whether to wait until the queue is empty
        # whether to cancel futures and clear database
        pass
