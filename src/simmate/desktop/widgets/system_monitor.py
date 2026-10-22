import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel

from simmate.desktop import theme
from simmate.desktop.widgets.dataset_browser import get_datasets_dir


class SystemMonitor(QLabel):
    """
    Live CPU, RAM and disk usage of this machine, for the window's status bar. The
    disk is the drive that holds the datasets folder (see `get_datasets_dir`).
    """

    INTERVAL_MS = 2000

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"color: {theme.MUTED_COLOR}; padding: 0 2px 0 8px;")
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.cores = psutil.cpu_count() or 1
        self.total_gb = psutil.virtual_memory().total / 1024**3
        self.datasets_dir = get_datasets_dir()
        # Wide enough for 100% use (and a full disk), so the label doesn't shift as
        # the numbers change.
        disk_gb = psutil.disk_usage(str(self.datasets_dir)).total / 1024**3
        self.setMinimumWidth(
            self.fontMetrics().horizontalAdvance(self._text(100, 100, disk_gb, disk_gb))
            + 16
        )

        # The first reading only starts the clock (it's always 0%), so take it now.
        psutil.cpu_percent()
        self.timer = QTimer(self, interval=self.INTERVAL_MS)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self):
        disk = psutil.disk_usage(str(self.datasets_dir))
        self.setText(
            self._text(
                psutil.cpu_percent(),
                psutil.virtual_memory().percent,
                disk.used / 1024**3,
                disk.free / 1024**3,
            )
        )

    def _text(self, cpu: float, ram: float, disk_used: float, disk_free: float) -> str:
        return (
            f"CPU {cpu:.0f}% of {self.cores} cores   │   "
            f"RAM {ram:.0f}% of {self.total_gb:.1f} GB   │   "
            f"Disk {disk_used:.1f} GB used · {disk_free:.1f} GB free"
        )
