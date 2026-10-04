from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderTab(QWidget):
    """A stand-in for a tab that hasn't been built yet."""

    status = Signal(str)

    def __init__(self, title: str):
        super().__init__()
        label = QLabel(f"<h2>{title}</h2><p>Coming soon</p>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #5f6368;")
        layout = QVBoxLayout(self)
        layout.addWidget(label)
