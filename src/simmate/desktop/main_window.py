# -*- coding: utf-8 -*-

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QTabWidget

from simmate.desktop.tabs import DashboardTab, ViewportTab
from simmate.desktop.widgets import TitleBar

# Width (px) of the invisible border you can drag to resize the window.
RESIZE_MARGIN = 5


class MainWindow(QMainWindow):
    """
    The top-level window of the Simmate desktop app. It holds each tab and
    owns the menu and status bar.

    The window is frameless so it can use our own teal `TitleBar`. Without the
    OS frame, it handles resizing itself through a thin margin around its edges.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simmate")
        self.resize(1400, 900)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMouseTracking(True)  # so the cursor changes over the resize margin
        self.setContentsMargins(*[RESIZE_MARGIN] * 4)

        self.title_bar = TitleBar(self)
        self.setMenuWidget(self.title_bar)

        tabs = QTabWidget()
        for tab, title in [
            (DashboardTab(), "Dashboard"),
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
        self.title_bar.menu_bar.addMenu("&File").addAction(quit_action)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.update_maximize_button()
            # A maximized window can't be resized, so drop the margin.
            margin = 0 if self.isMaximized() else RESIZE_MARGIN
            self.setContentsMargins(*[margin] * 4)
        super().changeEvent(event)

    def _edges_at(self, position) -> Qt.Edge:
        """Which window edges the point is within the resize margin of."""
        edges = Qt.Edge(0)
        if self.isMaximized():
            return edges
        if position.x() <= RESIZE_MARGIN:
            edges |= Qt.Edge.LeftEdge
        if position.x() >= self.width() - RESIZE_MARGIN:
            edges |= Qt.Edge.RightEdge
        if position.y() <= RESIZE_MARGIN:
            edges |= Qt.Edge.TopEdge
        if position.y() >= self.height() - RESIZE_MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    def mouseMoveEvent(self, event):
        edges = self._edges_at(event.position().toPoint())
        horizontal = edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge)
        vertical = edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge)
        if horizontal and vertical:
            forward = edges in (
                Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
                Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
            )
            cursor = (
                Qt.CursorShape.SizeFDiagCursor
                if forward
                else Qt.CursorShape.SizeBDiagCursor
            )
            self.setCursor(cursor)
        elif horizontal:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif vertical:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        edges = self._edges_at(event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and edges:
            # The OS does the actual resize, same as with a native frame.
            self.windowHandle().startSystemResize(edges)
            return
        super().mousePressEvent(event)
