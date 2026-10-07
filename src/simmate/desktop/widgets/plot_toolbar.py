import math

import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPixmap,
    QShortcut,
    QTransform,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.theme import rgba
from simmate.desktop.widgets.button import PrimaryButton, button_style

PANEL_STYLE = """
#settingsPanel {
    background: palette(base); border: 1px solid palette(mid); border-radius: 6px;
}
"""
GEAR_SIZE = 18  # px


class MouseModeToggle(QWidget):
    """Plotly-style Zoom/Pan switch, shared by every plot it's connected to.

    - Zoom mode (default): left-drag draws a box and zooms to it.
    - Pan mode: left-drag moves the view.
    - Scroll zooms and middle-drag pans in either mode.

    Emits `mode_changed(mode)` with a `pg.ViewBox` mouse mode; `mode` is the current one.
    """

    mode_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.mode = pg.ViewBox.RectMode

        # Zoom and Pan are one segmented control: exactly one is on at a time.
        zoom_button = PrimaryButton("Zoom", muted=True, objectName="segmentLeft")
        pan_button = PrimaryButton("Pan", muted=True, objectName="segmentRight")
        zoom_button.setToolTip("Drag a box on a plot to zoom into it")
        pan_button.setToolTip("Drag a plot to move its view")
        mode_group = QButtonGroup(self)
        for button, mode in [
            (zoom_button, pg.ViewBox.RectMode),
            (pan_button, pg.ViewBox.PanMode),
        ]:
            button.setCheckable(True)
            button.toggled.connect(lambda on, m=mode: on and self._set_mode(m))
            mode_group.addButton(button)
        zoom_button.setChecked(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(zoom_button)
        layout.addWidget(pan_button)

    def _set_mode(self, mode: int):
        self.mode = mode
        self.mode_changed.emit(mode)


class ResetViewButton(QToolButton):
    """A grey circular-arrow button that fits all of a PlotWidget's data again.

    Double-clicking the plot does the same.
    """

    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self.view_box = plot.getPlotItem().getViewBox()
        plot.hideButtons()  # pyqtgraph's tiny "A" autorange button; this replaces it
        plot.scene().sigMouseClicked.connect(self._on_click)
        self.setProperty("muted", True)  # grey, read by button_style
        self.setStyleSheet(button_style())
        self.setIcon(reset_icon())
        self.setIconSize(QSize(GEAR_SIZE, GEAR_SIZE))
        self.setToolTip("Reset the view to fit all the data (or double-click the plot)")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.reset_view)

    def reset_view(self):
        self.view_box.autoRange()

    def _on_click(self, event):
        if event.double():
            self.reset_view()


class _ClickCatcher(QWidget):
    """An invisible layer over the whole window that reports any click on it."""

    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()


class SettingsButton(QToolButton):
    """A gear button that toggles a floating panel of `content` (e.g. plot options).

    Pass `icon` to show something other than the gear (e.g. `columns_icon()`), and/or
    `text` to show a label, in the primary color (e.g. for a page's main action).

    `set_alert(True)` outlines the button in red (e.g. while a setting is missing).

    The panel floats inside the window, under the button's right edge (or its left
    edge, if there's no room on the left), rather than being a popup window: on Wayland, popup menus are positioned unreliably and can
    stop opening. While it's open, an invisible layer behind it covers the rest of
    the window, so clicking anywhere else (or the gear again) or pressing Escape
    closes it.
    """

    def __init__(
        self,
        content: QWidget,
        tooltip: str = "Settings",
        icon: QIcon | None = None,
        text: str = "",
    ):
        super().__init__()
        self.setProperty("muted", not text)  # grey, read by button_style
        self.setStyleSheet(
            button_style()
            # a text button is as wide as a PrimaryButton
            + ("QToolButton { padding: 4px 14px; }" if text else "")
            + f"""QToolButton[alert="true"] {{
                border-color: {theme.ERROR_COLOR};
                background: {rgba(theme.ERROR_COLOR, theme.HOVER_ALPHA)};
            }}"""
        )
        self.setToolTip(tooltip)
        self.is_gear = not (text or icon)  # only the gear turns red with an alert
        if text:
            self.setText(text)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if icon or not text:
            self.setIcon(icon or gear_icon())
            self.setIconSize(QSize(GEAR_SIZE, GEAR_SIZE))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)  # checked (filled) while the panel is open
        self.toggled.connect(self._set_panel_open)

        self.click_catcher = _ClickCatcher()
        self.click_catcher.clicked.connect(lambda: self.setChecked(False))
        self.click_catcher.hide()

        self.panel = QFrame(objectName="settingsPanel")
        self.panel.setStyleSheet(PANEL_STYLE)
        shadow = QGraphicsDropShadowEffect(blurRadius=16, offset=QPointF(0, 2))
        shadow.setColor(QColor(0, 0, 0, 60))
        self.panel.setGraphicsEffect(shadow)
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content)
        close_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self.panel)
        close_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        close_shortcut.activated.connect(lambda: self.setChecked(False))
        self.panel.hide()
        # The window shows a resize cursor over its edges, and children without a
        # cursor of their own keep showing whichever one it set last.
        for widget in (self.click_catcher, self.panel):
            widget.setCursor(Qt.CursorShape.ArrowCursor)

    def set_alert(self, alert: bool):
        """Outlines the button (and colors the gear) red, or back to normal."""
        self.setProperty("alert", alert)
        self.style().polish(self)  # re-read the stylesheet for the new property
        if self.is_gear:
            self.setIcon(gear_icon(color=theme.ERROR_COLOR if alert else None))

    def _set_panel_open(self, open: bool):
        window = self.window()
        if open:
            # Parented to the window only now, since the button may not have been
            # in one when it was made.
            for widget in (self.click_catcher, self.panel):
                widget.setParent(window)
            self._place_panel()
            self.click_catcher.show()
            self.panel.show()
            self.click_catcher.raise_()
            self.panel.raise_()
            self.panel.setFocus()
            window.installEventFilter(self)  # to follow window resizes
        else:
            window.removeEventFilter(self)
            self.click_catcher.hide()
            self.panel.hide()

    def _place_panel(self):
        self.click_catcher.setGeometry(self.window().rect())
        self.panel.adjustSize()
        bottom_right = self.mapTo(self.window(), self.rect().bottomRight())
        x = bottom_right.x() - self.panel.width() + 1
        if x < 0:  # no room on the left, so line up with the button's left edge
            x = self.mapTo(self.window(), self.rect().topLeft()).x()
        x = min(x, self.window().width() - self.panel.width())  # nor the right
        self.panel.move(max(x, 0), bottom_right.y() + 4)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self._place_panel()
        return False


def gear_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A gear in grey (or `color`), or in white when the button is checked."""
    return _icon(_gear_path(size), size, color)


def columns_icon(size: int = GEAR_SIZE) -> QIcon:
    """Three side-by-side columns, like `gear_icon` (e.g. for choosing table columns)."""
    return _icon(_columns_path(size), size)


def reset_icon(size: int = GEAR_SIZE) -> QIcon:
    """A circular arrow, like `gear_icon` (e.g. for resetting a value to its default)."""
    return _icon(_reset_path(size), size)


def plus_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A plus sign, like `gear_icon` (e.g. for adding something)."""
    return _icon(_plus_path(size), size, color)


def stop_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A rounded square, like `gear_icon` (e.g. for stopping something running)."""
    return _icon(_stop_path(size), size, color)


def trash_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A trash can, like `gear_icon` (e.g. for deleting something)."""
    return _icon(_trash_path(size), size, color)


def folder_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A folder."""
    return _icon(_folder_path(size), size, color)


def download_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """An arrow pointing down onto a tray."""
    return _icon(_download_path(size), size, color)


def lock_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """A padlock (e.g. for locking/unlocking a layout)."""
    return _icon(_lock_path(size), size, color)


def grip_icon(size: int = GEAR_SIZE, color: str | None = None) -> QIcon:
    """Two columns of three dots (e.g. a handle to drag something by)."""
    return _icon(_grip_path(size), size, color)


def _icon(path: QPainterPath, size: int, color: str | None = None) -> QIcon:
    """`path` filled in grey (or `color`), or in white when the button is checked."""
    icon = QIcon()
    for color, state in [
        (color or theme.MUTED_COLOR, QIcon.State.Off),
        ("white", QIcon.State.On),
    ]:
        pixmap = _pixmap(path, size, QColor(color))
        for mode in (QIcon.Mode.Normal, QIcon.Mode.Active):
            icon.addPixmap(pixmap, mode, state)
    return icon


def _pixmap(path: QPainterPath, size: int, color: QColor) -> QPixmap:
    scale = 3  # drawn large so it stays crisp on high-DPI screens
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillPath(path, color)
    painter.end()
    return pixmap


def _gear_path(size: int) -> QPainterPath:
    center = QPointF(size / 2, size / 2)
    gear = QPainterPath()
    gear.addEllipse(center, size * 0.32, size * 0.32)
    tooth_width, tooth_length = size * 0.18, size * 0.46
    for i in range(8):
        tooth = QPainterPath()
        tooth.addRect(
            QRectF(-tooth_width / 2, -tooth_length, tooth_width, tooth_length)
        )
        transform = QTransform().translate(center.x(), center.y()).rotate(i * 45)
        gear = gear.united(transform.map(tooth))
    hole = QPainterPath()
    hole.addEllipse(center, size * 0.14, size * 0.14)
    return gear.subtracted(hole)


def _columns_path(size: int) -> QPainterPath:
    width, gap, height = size * 0.24, size * 0.1, size * 0.8
    left = (size - 3 * width - 2 * gap) / 2
    top = (size - height) / 2
    columns = QPainterPath()
    for i in range(3):
        rect = QRectF(left + i * (width + gap), top, width, height)
        columns.addRoundedRect(rect, size * 0.06, size * 0.06)
    return columns


def _reset_path(size: int) -> QPainterPath:
    # An open ring (counter-clockwise from its end at the top-right) with an
    # arrowhead on that end. Qt angles run counter-clockwise from 3 o'clock.
    radius, width = size * 0.3, size * 0.12
    center = QPointF(size / 2, size / 2)
    start, sweep = 70, 290
    circle = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
    arc = QPainterPath()
    arc.arcMoveTo(circle, start)
    arc.arcTo(circle, start, sweep)
    stroker = QPainterPathStroker()
    stroker.setWidth(width)
    stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
    ring = stroker.createStroke(arc)

    # The arrowhead sits on the ring's start and points back along it (clockwise).
    angle = math.radians(start)
    outward = QPointF(math.cos(angle), -math.sin(angle))
    forward = QPointF(math.sin(angle), math.cos(angle))  # clockwise tangent
    end = center + outward * radius
    head = QPainterPath(end + outward * width * 1.6)
    head.lineTo(end + forward * width * 2)
    head.lineTo(end - outward * width * 1.6)
    head.closeSubpath()
    return ring.united(head)


def _plus_path(size: int) -> QPainterPath:
    length, width = size * 0.7, size * 0.14
    plus = QPainterPath()
    plus.addRoundedRect(
        QRectF((size - length) / 2, (size - width) / 2, length, width),
        width / 2,
        width / 2,
    )
    vertical = QPainterPath()
    vertical.addRoundedRect(
        QRectF((size - width) / 2, (size - length) / 2, width, length),
        width / 2,
        width / 2,
    )
    return plus.united(vertical)


def _stop_path(size: int) -> QPainterPath:
    side = size * 0.56
    stop = QPainterPath()
    stop.addRoundedRect(
        QRectF((size - side) / 2, (size - side) / 2, side, side),
        size * 0.08,
        size * 0.08,
    )
    return stop


def _trash_path(size: int) -> QPainterPath:
    # a lid with a handle, over a can that narrows to the bottom, with two slots
    radius = size * 0.04
    trash = QPainterPath()
    trash.addRoundedRect(
        QRectF(size * 0.16, size * 0.2, size * 0.68, size * 0.1), radius, radius
    )
    trash.addRoundedRect(
        QRectF(size * 0.38, size * 0.1, size * 0.24, size * 0.14), radius, radius
    )
    can = QPainterPath(QPointF(size * 0.24, size * 0.36))
    can.lineTo(size * 0.76, size * 0.36)
    can.lineTo(size * 0.7, size * 0.9)
    can.lineTo(size * 0.3, size * 0.9)
    can.closeSubpath()
    for x in (0.4, 0.55):
        slot = QPainterPath()
        slot.addRoundedRect(
            QRectF(size * x, size * 0.46, size * 0.06, size * 0.34), radius, radius
        )
        can = can.subtracted(slot)
    return trash.united(can)


def _folder_path(size: int) -> QPainterPath:
    # a tab on the top-left, over the folder's body
    radius = size * 0.06
    folder = QPainterPath()
    folder.addRoundedRect(
        QRectF(size * 0.1, size * 0.2, size * 0.34, size * 0.2), radius, radius
    )
    folder.addRoundedRect(
        QRectF(size * 0.1, size * 0.3, size * 0.8, size * 0.52), radius, radius
    )
    return folder.simplified()


def _download_path(size: int) -> QPainterPath:
    # a shaft and arrowhead pointing down, over an open tray
    width = size * 0.12
    arrow = QPainterPath()
    arrow.addRect(QRectF((size - width) / 2, size * 0.1, width, size * 0.36))
    head = QPainterPath(QPointF(size * 0.26, size * 0.42))
    head.lineTo(size * 0.74, size * 0.42)
    head.lineTo(size * 0.5, size * 0.68)
    head.closeSubpath()
    tray = QPainterPath(QPointF(size * 0.14, size * 0.64))
    tray.lineTo(size * 0.14, size * 0.88)
    tray.lineTo(size * 0.86, size * 0.88)
    tray.lineTo(size * 0.86, size * 0.64)
    stroker = QPainterPathStroker()
    stroker.setWidth(width)
    stroker.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    stroker.setCapStyle(Qt.PenCapStyle.RoundCap)
    return arrow.united(head).united(stroker.createStroke(tray))


def _lock_path(size: int) -> QPainterPath:
    # a rounded body with a keyhole, under an arched shackle
    radius = size * 0.08
    body = QPainterPath()
    body.addRoundedRect(
        QRectF(size * 0.18, size * 0.44, size * 0.64, size * 0.46), radius, radius
    )
    keyhole = QPainterPath()
    keyhole.addEllipse(QPointF(size * 0.5, size * 0.64), size * 0.07, size * 0.07)
    body = body.subtracted(keyhole)
    arch = QPainterPath(QPointF(size * 0.32, size * 0.46))
    arch.lineTo(size * 0.32, size * 0.32)
    arch.arcTo(QRectF(size * 0.32, size * 0.12, size * 0.36, size * 0.36), 180, -180)
    arch.lineTo(size * 0.68, size * 0.46)
    stroker = QPainterPathStroker()
    stroker.setWidth(size * 0.11)
    stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
    return body.united(stroker.createStroke(arch))


def _grip_path(size: int) -> QPainterPath:
    grip = QPainterPath()
    for x in (0.38, 0.62):
        for y in (0.26, 0.5, 0.74):
            grip.addEllipse(QPointF(size * x, size * y), size * 0.08, size * 0.08)
    return grip
