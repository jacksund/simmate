# -*- coding: utf-8 -*-

from concurrent.futures import Future

# class based on...
# https://docs.python.org/3/library/concurrent.futures.html


class DjangoFuture(Future):
    def __init__(self):
        pass

    def cancel(self):
        """
        Attempt to cancel the call. If the call is currently being executed or
        finished running and cannot be cancelled then the method will return
        False, otherwise the call will be cancelled and the method will return
        True.
        """
        pass

    def cancelled(self):
        """
        Return True if the call was successfully cancelled.
        """
        pass

    def running(self):
        """
        Return True if the call is currently being executed and cannot be cancelled.
        """
        pass

    def done(self):
        """
        Return True if the call was successfully cancelled or finished running.
        """
        pass

    def result(self, timeout=None):
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
        pass

    def exception(self, timeout=None):
        """
        Return the exception raised by the call. If the call hasn’t yet
        completed then this method will wait up to timeout seconds. If the call
        hasn’t completed in timeout seconds, then a concurrent.futures.TimeoutError
        will be raised. timeout can be an int or float. If timeout is not
        specified or None, there is no limit to the wait time.

        If the future is cancelled before completing then CancelledError
        will be raised.

        If the call completed without raising, None is returned.
        """
        pass

    def add_done_callback(self, fn):
        """
        Attaches the callable fn to the future. fn will be called, with the
        future as its only argument, when the future is cancelled or finishes
        running.

        Added callables are called in the order that they were added and are
        always called in a thread belonging to the process that added them. If
        the callable raises an Exception subclass, it will be logged and
        ignored. If the callable raises a BaseException subclass, the behavior
        is undefined.

        If the future has already completed or been cancelled, fn will be
        called immediately.
        """
        pass

    # ------------------------------------------------------------------------

    # these methods are for use by the Executor only

    def set_running_or_notify_cancel(self):
        """
        This method should only be called by Executor implementations before
        executing the work associated with the Future and by unit tests.

        If the method returns False then the Future was cancelled, i.e.
        Future.cancel() was called and returned True. Any threads waiting on
        the Future completing (i.e. through as_completed() or wait()) will
        be woken up.

        If the method returns True then the Future was not cancelled and has
        been put in the running state, i.e. calls to Future.running() will
        return True.

        This method can only be called once and cannot be called after
        Future.set_result() or Future.set_exception() have been called.
        """
        pass

    def set_result(self, result):
        """
        Sets the result of the work associated with the Future to result.

        This method should only be used by Executor implementations and unit tests.

        Changed in version 3.8: This method raises concurrent.futures.InvalidStateError
        if the Future is already done.
        """
        pass

    def set_exception(self, exception):
        """
        Sets the result of the work associated with the Future to the Exception
        exception.

        This method should only be used by Executor implementations and unit
        tests.

        Changed in version 3.8: This method raises
        concurrent.futures.InvalidStateError if the Future is already done.
        """
        pass
