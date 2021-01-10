# -*- coding: utf-8 -*-

# _FUTURE_STATES = [
#     PENDING,
#     RUNNING,
#     CANCELLED,
#     CANCELLED_AND_NOTIFIED,
#     FINISHED
# ]

from queue import Queue

# class based on...
# https://docs.python.org/3/library/queue.html


class DjangoQueue(Queue):
    def __init__(self):
        """"""
        pass

    def qsize(self):
        """
        Return the approximate size of the queue. Note, qsize() > 0 doesn’t
        guarantee that a subsequent get() will not block, nor will
        qsize() < maxsize guarantee that put() will not block.
        """
        pass

    def empty(self):
        """
        Return True if the queue is empty, False otherwise. If empty() returns
        True it doesn’t guarantee that a subsequent call to put() will not
        block. Similarly, if empty() returns False it doesn’t guarantee that
        a subsequent call to get() will not block.
        """
        pass

    def full(self):
        """
        Return True if the queue is full, False otherwise. If full() returns
        True it doesn’t guarantee that a subsequent call to get() will not
        block. Similarly, if full() returns False it doesn’t guarantee that a
        subsequent call to put() will not block.
        """
        pass

    def put(self, item, block=True, timeout=None):
        """
        Put item into the queue. If optional args block is true and timeout is
        None (the default), block if necessary until a free slot is available.
        If timeout is a positive number, it blocks at most timeout seconds and
        raises the Full exception if no free slot was available within that
        time. Otherwise (block is false), put an item on the queue if a free
        slot is immediately available, else raise the Full exception
        (timeout is ignored in that case).
        """
        pass

    def put_nowait(self, item):
        """
        Equivalent to put(item, False).
        """
        pass

    def get(self, block=True, timeout=None):
        """
        Remove and return an item from the queue. If optional args block is
        true and timeout is None (the default), block if necessary until an
        item is available. If timeout is a positive number, it blocks at most
        timeout seconds and raises the Empty exception if no item was available
        within that time. Otherwise (block is false), return an item if one is
        immediately available, else raise the Empty exception
        (timeout is ignored in that case).

        Prior to 3.0 on POSIX systems, and for all versions on Windows, if
        block is true and timeout is None, this operation goes into an
        uninterruptible wait on an underlying lock. This means that no
        exceptions can occur, and in particular a SIGINT will not trigger a
        KeyboardInterrupt.
        """
        pass

    def get_nowait(self):
        """
        Two methods are offered to support tracking whether enqueued tasks
        have been fully processed by daemon consumer threads.
        """
        pass

    def task_done(self):
        """
        Indicate that a formerly enqueued task is complete. Used by queue
        consumer threads. For each get() used to fetch a task, a subsequent
        call to task_done() tells the queue that the processing on the task
        is complete.

        If a join() is currently blocking, it will resume when all items have
        been processed (meaning that a task_done() call was received for every
                        item that had been put() into the queue).

        Raises a ValueError if called more times than there were items placed
        in the queue.
        """
        pass

    def join(self):
        """
        Blocks until all items in the queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate that the item was retrieved and all work on it is complete.
        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        pass
