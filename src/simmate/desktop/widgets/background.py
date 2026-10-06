import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal


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
