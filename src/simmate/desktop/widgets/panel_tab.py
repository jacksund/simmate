from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen, QTransform
from PySide6.QtWidgets import QAbstractButton, QStackedWidget, QVBoxLayout, QWidget

from simmate.desktop.theme import (
    HOVER_ALPHA,
    PRESSED_ALPHA,
    PRIMARY_COLOR,
    PRIMARY_DARKER,
    PRIMARY_LIGHTER,
    tint,
)


class PanelTab(QAbstractButton):
    """One pull tab on the inner edge of a side panel.

    Checked means its page is the one open: filled in the primary color. Otherwise
    it's a primary-color outline. The label runs vertically so the tab stays narrow.
    `side` is the side of the window the panel is on: the tab is square where it
    meets the panel and rounded on the far side.
    """

    WIDTH = 28
    RADIUS = 6
    OUTLINE_WIDTH = 1.5

    def __init__(self, text: str, side: str = "left"):
        super().__init__()
        self.side = side  # "left" or "right"
        self.setText(text)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def sizeHint(self) -> QSize:
        text_length = QFontMetrics(self.font()).horizontalAdvance(self.text())
        return QSize(self.WIDTH, text_length + 24)  # 12px padding at each end

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Inset by half the outline so it isn't clipped (except where the tab meets
        # the tab bar's line).
        inset = self.OUTLINE_WIDTH / 2
        rect = QRectF(self.rect()).adjusted(0, inset, -inset, -inset)

        # Drawn for a left panel: square on the left so it reads as attached to the
        # panel, rounded on the right. Mirrored for a right panel.
        r = self.RADIUS
        path = QPainterPath()
        path.moveTo(rect.topLeft())
        path.lineTo(rect.right() - r, rect.top())
        path.quadTo(rect.topRight(), QPointF(rect.right(), rect.top() + r))
        path.lineTo(rect.right(), rect.bottom() - r)
        path.quadTo(rect.bottomRight(), QPointF(rect.right() - r, rect.bottom()))
        path.lineTo(rect.bottomLeft())
        if self.side == "right":
            path = QTransform(-1, 0, 0, 1, self.width(), 0).map(path)
            rect.moveLeft(inset)

        if self.isChecked():
            if self.isDown():
                fill = QColor(PRIMARY_DARKER)
            elif self.underMouse():
                fill = QColor(PRIMARY_LIGHTER)
            else:
                fill = QColor(PRIMARY_COLOR)
            painter.fillPath(path, fill)
            content_color = QColor("white")
        else:
            if self.isDown() or self.underMouse():
                alpha = PRESSED_ALPHA if self.isDown() else HOVER_ALPHA
                painter.fillPath(path, tint(PRIMARY_COLOR, alpha))
            painter.setPen(QPen(QColor(PRIMARY_COLOR), self.OUTLINE_WIDTH))
            painter.drawPath(path)
            content_color = QColor(PRIMARY_COLOR)

        # Label, rotated to read top-to-bottom, centered in the tab.
        painter.setPen(content_color)
        painter.translate(rect.center())
        painter.rotate(90)
        text_rect = QRectF(
            -rect.height() / 2, -rect.width() / 2, rect.height(), rect.width()
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())


class SideTabBar(QWidget):
    """A column of pull tabs on a side panel's inner edge, with a separator line.

    At most one tab is open at a time. Clicking a closed tab switches to it, and
    clicking the open one closes it (leaving none open, i.e. the panel collapsed).
    `current_changed` fires with the open tab's index, or -1 when none is.
    """

    current_changed = Signal(int)

    LINE_WIDTH = 2

    def __init__(self, titles: list[str], side: str = "left"):
        super().__init__()
        self.side = side  # which side of the window the panel is on
        self.setFixedWidth(PanelTab.WIDTH)
        self._current = -1

        self.tabs = [PanelTab(title, side) for title in titles]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for i, tab in enumerate(self.tabs):
            tab.clicked.connect(lambda _, i=i: self._on_tab_clicked(i))
            layout.addWidget(tab)
        layout.addStretch()

    def current(self) -> int:
        return self._current

    def set_current(self, index: int, emit: bool = True):
        self._current = index
        for i, tab in enumerate(self.tabs):
            tab.setChecked(i == index)
        if emit:
            self.current_changed.emit(index)

    def _on_tab_clicked(self, index: int):
        # The click already toggled the tab itself; set_current re-applies all states.
        self.set_current(-1 if index == self._current else index)

    def paintEvent(self, event):
        # The separator line, along the tabs' base (the panel side) for the full height.
        painter = QPainter(self)
        x = 0 if self.side == "left" else self.width() - self.LINE_WIDTH
        painter.fillRect(
            QRectF(x, 0, self.LINE_WIDTH, self.height()), QColor(PRIMARY_COLOR)
        )


class SidePanel(QStackedWidget):
    """A side panel's pages, plus the tab bar that switches between them.

    Add `self.tabs` to the layout right beside the panel (outside the splitter, so
    the tabs stay visible when the panel collapses). The first page starts open.
    """

    def __init__(
        self,
        pages: list[tuple[str, QWidget]],
        side: str,
        width: int,
        min_width: int,
    ):
        super().__init__()
        self.open_width = width  # restored when the collapsed panel is reopened
        self.min_width = min_width
        for _, page in pages:
            self.addWidget(page)
        self.tabs = SideTabBar([title for title, _ in pages], side)
        self.tabs.set_current(0, emit=False)

    def minimumSizeHint(self) -> QSize:
        # While open, it can't be squeezed below `min_width` (it can still collapse
        # fully). Once collapsed it needs no space, so it doesn't hold the window
        # wide. Call updateGeometry() after opening/closing so the splitter re-reads it.
        hint = super().minimumSizeHint()
        width = self.min_width if self.tabs.current() >= 0 else 0
        return QSize(width, hint.height())
