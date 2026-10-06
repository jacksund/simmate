# -*- coding: utf-8 -*-

from collections.abc import Callable

from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPainter, QPainterPath
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from simmate.desktop import theme
from simmate.desktop.tabs import DashboardTab, DatasetsTab, WorkersTab
from simmate.desktop.widgets import SystemMonitor, TitleBar

# Width (px) of the invisible border you can drag to resize the window.
RESIZE_MARGIN = 5

# The resize cursor for each edge (or corner) of that border.
EDGE_CURSORS = {
    Qt.Edge.LeftEdge: Qt.CursorShape.SizeHorCursor,
    Qt.Edge.RightEdge: Qt.CursorShape.SizeHorCursor,
    Qt.Edge.TopEdge: Qt.CursorShape.SizeVerCursor,
    Qt.Edge.BottomEdge: Qt.CursorShape.SizeVerCursor,
    Qt.Edge.TopEdge | Qt.Edge.LeftEdge: Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.BottomEdge | Qt.Edge.RightEdge: Qt.CursorShape.SizeFDiagCursor,
    Qt.Edge.TopEdge | Qt.Edge.RightEdge: Qt.CursorShape.SizeBDiagCursor,
    Qt.Edge.BottomEdge | Qt.Edge.LeftEdge: Qt.CursorShape.SizeBDiagCursor,
}


def tab_style() -> str:
    """Flat tabs with a teal underline on the selected one. Set on the window, so it
    also covers tab widgets nested inside the tabs."""
    return f"""
QTabWidget::pane {{ border: none; border-top: 1px solid palette(mid); top: -1px; }}
QTabWidget::tab-bar {{ left: 8px; }}
QTabBar::tab {{
    background: transparent; color: {theme.MUTED_COLOR};
    border: none; border-bottom: 2px solid transparent;
    padding: 8px 16px; margin-right: 4px; font-weight: 600;
}}
QTabBar::tab:hover {{ color: palette(text); border-bottom-color: palette(mid); }}
QTabBar::tab:selected {{
    color: {theme.PRIMARY_COLOR}; border-bottom-color: {theme.PRIMARY_COLOR};
}}
"""


class MainWindow(QMainWindow):
    """
    The top-level window of the Simmate desktop app. It holds each tab and
    owns the status bar.

    The window is frameless so it can use our own teal `TitleBar`. Without the
    OS frame, it handles resizing itself through a thin margin around its edges.

    Apps built on Simmate can subclass this and override `get_tabs`.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(theme.APP_NAME)
        self.setWindowIcon(QIcon(str(theme.ICON_PATH)))
        self.resize(1400, 900)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        # A see-through window lets us round its corners in paintEvent. The resize
        # margin stays invisible but still catches the mouse.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)  # so the cursor changes over the resize margin
        self.setContentsMargins(*[RESIZE_MARGIN] * 4)

        self.setStyleSheet(tab_style())

        self.title_bar = TitleBar()
        self.setMenuWidget(self.title_bar)

        tabs = QTabWidget()
        for title, make_tab in self.get_tabs():
            tab = make_tab()
            # Each tab reports what it's doing via a signal; the window owns the status bar.
            tab.status.connect(self.statusBar().showMessage)
            tabs.addTab(tab, title)
        self.setCentralWidget(tabs)

        # The window shows a resize cursor over its margin. Give its children a
        # normal arrow so they don't inherit that cursor once the mouse moves in.
        for child in [self.title_bar, tabs, self.statusBar()]:
            child.setCursor(Qt.CursorShape.ArrowCursor)
        tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)

        # Messages show on the left; machine usage stays on the right.
        self.statusBar().addPermanentWidget(SystemMonitor())
        # The window's edges already resize it, so skip the grip in the corner. That
        # also lets the text on each side sit the same distance from the edge.
        self.statusBar().setSizeGripEnabled(False)
        # Extra room below the text, which otherwise sits low against the window's edge.
        self.statusBar().setContentsMargins(0, 0, 0, 4)
        # Messages in the same grey as the usage readout.
        self.statusBar().setStyleSheet(f"QStatusBar {{ color: {theme.MUTED_COLOR}; }}")

        self._add_shortcuts()
        self.statusBar().showMessage("Ready")

    def get_tabs(self) -> list[tuple[str, Callable[[], QWidget]]]:
        """
        The (title, factory) pairs of the tabs to show, in order. Each factory
        (e.g. a class) builds its tab, so an override can add, drop, or swap tabs
        without building the ones it replaces. Each tab needs a
        `status = Signal(str)`, like `PlaceholderTab`.
        """
        return [
            ("Datasets", DatasetsTab),
            ("Toolkit", DashboardTab),
            ("Workers", WorkersTab),
        ]

    def _add_shortcuts(self):
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

    def paintEvent(self, event):
        # Fill the area inside the resize margin with the normal window color,
        # rounding the corners unless maximized.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 0 if self.isMaximized() else theme.CORNER_RADIUS
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.contentsRect()), radius, radius)
        painter.fillPath(path, self.palette().window())

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
        cursor = EDGE_CURSORS.get(self._edges_at(event.position().toPoint()))
        if cursor is None:
            self.unsetCursor()
        else:
            self.setCursor(cursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        edges = self._edges_at(event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and edges:
            # The OS does the actual resize, same as with a native frame.
            self.windowHandle().startSystemResize(edges)
            return
        super().mousePressEvent(event)
