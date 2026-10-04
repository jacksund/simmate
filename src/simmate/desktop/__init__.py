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
    import pyqtgraph as pg
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from simmate.desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    # Always use light mode: Ketcher and the molecule images have white
    # backgrounds, so following a dark system theme looks bad. Fusion's standard
    # palette is a fallback for Linux themes that still push a dark palette.
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    pg.setConfigOptions(background="w", foreground="k")

    window = MainWindow()
    window.show()
    # Hand control to Qt's event loop; it runs until the last window closes.
    sys.exit(app.exec())
