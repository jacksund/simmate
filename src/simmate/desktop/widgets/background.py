import threading
import time
from collections.abc import Callable, Iterator

from PySide6.QtCore import QObject, QTimer, Signal


class BackgroundTask(QObject):
    """
    Runs `work(task)` on a background thread, so slow work (a download, a file
    conversion) doesn't freeze the window. Its signals arrive on the UI thread:
    `finished` with what `work` returned, or `failed` with the error's message.

    `work` may report progress with `task.progress.emit(done, total)` and should
    stop early once `task.cancelled` is set (by `cancel()`). Give the task a parent
    widget so it stays alive while it runs.
    """

    progress = Signal(int, int)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, work: Callable[["BackgroundTask"], object], parent=None):
        super().__init__(parent)
        self.work = work
        self.cancelled = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def cancel(self):
        self.cancelled = True

    def _run(self):
        try:
            result = self.work(self)
        except Exception as error:
            self.failed.emit(str(error) or type(error).__name__)
        else:
            self.finished.emit(result)


class IncrementalTask(QObject):
    """
    Runs `steps` (a generator yielding how much is done) a slice at a time on the
    UI thread, between events, so the window stays responsive.

    Use this rather than `BackgroundTask` for long work that runs a lot of Python
    (e.g. a loop over every molecule): on a background thread it would hold
    Python's GIL, which stalls the window wherever Qt calls back into Python (e.g.
    painting the table or filtering its rows).

    It reports `progress(done, total)` after each slice, then `finished`, or
    `failed` with the error's message. It stops when cancelled or deleted (e.g.
    with its parent).
    """

    progress = Signal(int, int)
    finished = Signal()
    failed = Signal(str)

    SLICE = 0.015  # seconds of work between UI events

    def __init__(self, steps: Iterator[int], total: int, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.total = total
        self.timer = QTimer(self, interval=0)
        self.timer.timeout.connect(self._step)

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.stop()

    def _step(self):
        end = time.perf_counter() + self.SLICE
        done = 0
        try:
            while time.perf_counter() < end:
                done = next(self.steps)
        except StopIteration:
            self.timer.stop()
            self.finished.emit()
            return
        except Exception as error:
            self.timer.stop()
            self.failed.emit(str(error) or type(error).__name__)
            return
        self.progress.emit(done, self.total)
