# -*- coding: utf-8 -*-

"""
A Qt-based (PySide6) desktop app for exploring chemical data.

Launch it with `simmate desktop start`, or build a standalone executable
with `simmate desktop build`. Requires the `desktop` extra dependencies.
"""

import sys


def main() -> None:
    """
    Starts the desktop app and blocks until the window is closed.
    """
    from PySide6.QtWidgets import QApplication

    from simmate.desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Hand control to Qt's event loop; it runs until the last window closes.
    sys.exit(app.exec())
