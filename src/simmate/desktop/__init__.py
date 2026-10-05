# -*- coding: utf-8 -*-

"""
A Qt-based (PySide6) desktop app for exploring chemical data.

Launch it with `simmate desktop start`, or build a standalone executable
with `simmate desktop build`. Requires the `desktop` extra dependencies.

Apps built on Simmate can make their own version of it without forking: rebrand
it with `simmate.desktop.theme.configure`, subclass `MainWindow` (e.g. to override
`get_tabs`), launch it with `main(window_class=...)`, and package it with
`simmate.desktop.build.build_executable`.
"""

import sys


def main(window_class: type | None = None) -> None:
    """
    Starts the desktop app and blocks until the window is closed.

    `window_class` is the main window to show, which defaults to `MainWindow`.
    """
    import pyqtgraph as pg
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
    from PySide6.QtWidgets import QApplication

    # Ketcher's web view draws through Qt Quick, which defaults to Direct3D on
    # Windows, while the 3D viewer is an OpenGL widget. A window can only compose
    # one graphics API, so without this the sketcher is a blank, see-through hole
    # on Windows. (Linux already defaults to OpenGL.) Both must be set before the
    # app is created; Qt WebEngine also needs shared contexts to run on OpenGL.
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    # Always use light mode: Ketcher and the molecule images have white
    # backgrounds, so following a dark system theme looks bad. Fusion's standard
    # palette is a fallback for Linux themes that still push a dark palette.
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
    pg.setConfigOptions(background="w", foreground="k")

    if window_class is None:
        from simmate.desktop.main_window import MainWindow as window_class

    window = window_class()
    window.show()
    # Hand control to Qt's event loop; it runs until the last window closes.
    sys.exit(app.exec())
