# -*- coding: utf-8 -*-

import signal
import threading
from contextlib import contextmanager


@contextmanager
def handle_sigterm():
    """
    Converts SIGTERM into a `KeyboardInterrupt` so that it is handled the same
    way as crtl+c (SIGINT).

    This is needed in containers (docker, k8s) because they stop processes
    with SIGTERM. Python does not handle SIGTERM by default, and when running
    as PID 1 in a container, the signal is ignored entirely -- meaning the
    process is eventually force-killed (SIGKILL) without any clean up.

    The handler is only installed when called from the main thread, as python
    only allows signal handlers to be set there. The original handler is
    restored on exit.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def _raise_interrupt(signum, frame):
        # ignore any repeated SIGTERMs so they don't interrupt our clean up
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise KeyboardInterrupt("SIGTERM received")

    original_handler = signal.signal(signal.SIGTERM, _raise_interrupt)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, original_handler)
