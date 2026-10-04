# -*- coding: utf-8 -*-

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QTabWidget

from simmate.desktop.tabs import (
    LinkedTab,
    MoleculeTab,
    SarTab,
    SketcherTab,
    TableTab,
    ViewportTab,
)


class MainWindow(QMainWindow):
    """
    The top-level window of the Simmate desktop app. It holds each tab and
    owns the menu and status bar.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simmate")
        self.resize(1000, 700)

        tabs = QTabWidget()
        for tab, title in [
            (MoleculeTab(), "Molecule"),
            (SketcherTab(), "Sketcher"),
            (SarTab(), "SAR"),
            (TableTab(), "Table"),
            (LinkedTab(), "Linked"),
            (ViewportTab(), "3D"),
        ]:
            # Each tab reports what it's doing via a signal; the window owns the status bar.
            tab.status.connect(self.statusBar().showMessage)
            tabs.addTab(tab, title)
        self.setCentralWidget(tabs)

        self._build_menu()
        self.statusBar().showMessage("Ready")

    def _build_menu(self):
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        self.menuBar().addMenu("&File").addAction(quit_action)
