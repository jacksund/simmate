import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel

from simmate.desktop.theme import MUTED_COLOR


class SystemMonitor(QLabel):
    """Live CPU and RAM usage of this machine, for the window's status bar."""

    INTERVAL_MS = 2000

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"color: {MUTED_COLOR}; padding: 0 2px 0 8px;")
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cores = psutil.cpu_count() or 1
        self.total_gb = psutil.virtual_memory().total / 1024**3
        # Wide enough for 100% use, so the label doesn't shift as the numbers change.
        self.setMinimumWidth(
            self.fontMetrics().horizontalAdvance(self._text(100, 100)) + 16
        )

        # The first reading only starts the clock (it's always 0%), so take it now.
        psutil.cpu_percent()
        self.timer = QTimer(self, interval=self.INTERVAL_MS)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        self.setText(self._text(psutil.cpu_percent(), psutil.virtual_memory().percent))

    def _text(self, cpu: float, ram: float) -> str:
        return (
            f"CPU {cpu:.0f}% of {self.cores} cores   │   "
            f"RAM {ram:.0f}% of {self.total_gb:.1f} GB"
        )
