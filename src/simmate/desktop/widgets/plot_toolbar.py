import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
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

from simmate.desktop.theme import MUTED_COLOR
from simmate.desktop.widgets.button import BUTTON_STYLE, PrimaryButton

PANEL_STYLE = f"""
#settingsPanel {{
    background: palette(base); border: 1px solid palette(mid); border-radius: 6px;
}}
"""
GEAR_SIZE = 18  # px


class PlotToolbar(QWidget):
    """Plotly-style controls for a PlotWidget.

    - Zoom mode (default): left-drag draws a box and zooms to it.
    - Pan mode: left-drag moves the view.
    - Scroll zooms and middle-drag pans in either mode.
    - "Reset" or double-clicking the plot fits all the data again.
    """

    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self.view_box = plot.getPlotItem().getViewBox()
        plot.hideButtons()  # pyqtgraph's tiny "A" autorange button; Reset replaces it
        plot.scene().sigMouseClicked.connect(self._on_click)

        # Zoom and Pan are one segmented control: exactly one is on at a time.
        zoom_button = PrimaryButton("Zoom", muted=True, objectName="segmentLeft")
        pan_button = PrimaryButton("Pan", muted=True, objectName="segmentRight")
        zoom_button.setToolTip("Drag a box to zoom into it")
        pan_button.setToolTip("Drag to move the view")
        mode_group = QButtonGroup(self)
        for button, mode in [
            (zoom_button, pg.ViewBox.RectMode),
            (pan_button, pg.ViewBox.PanMode),
        ]:
            button.setCheckable(True)
            button.toggled.connect(
                lambda on, m=mode: on and self.view_box.setMouseMode(m)
            )
            mode_group.addButton(button)
        zoom_button.setChecked(True)

        reset_button = PrimaryButton("Reset", muted=True)
        reset_button.setToolTip("Fit all points (or double-click the plot)")
        reset_button.clicked.connect(self.reset_view)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(zoom_button)
        layout.addWidget(pan_button)
        layout.addSpacing(8)
        layout.addWidget(reset_button)

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

    The panel floats inside the window, under the button's right edge, rather than
    being a popup window: on Wayland, popup menus are positioned unreliably and can
    stop opening. While it's open, an invisible layer behind it covers the rest of
    the window, so clicking anywhere else (or the gear again) or pressing Escape
    closes it.
    """

    def __init__(self, content: QWidget, tooltip: str = "Settings"):
        super().__init__()
        self.setProperty("muted", True)  # grey, read by BUTTON_STYLE
        self.setStyleSheet(BUTTON_STYLE)
        self.setToolTip(tooltip)
        self.setIcon(gear_icon())
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
        self.panel.move(bottom_right.x() - self.panel.width() + 1, bottom_right.y() + 4)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self._place_panel()
        return False


def gear_icon(size: int = GEAR_SIZE) -> QIcon:
    """A gear in grey, or in white when the button is checked."""
    icon = QIcon()
    for color, state in [
        (MUTED_COLOR, QIcon.State.Off),
        ("white", QIcon.State.On),
    ]:
        pixmap = _gear_pixmap(size, QColor(color))
        for mode in (QIcon.Mode.Normal, QIcon.Mode.Active):
            icon.addPixmap(pixmap, mode, state)
    return icon


def _gear_pixmap(size: int, color: QColor) -> QPixmap:
    scale = 3  # drawn large so it stays crisp on high-DPI screens
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)

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
    gear = gear.subtracted(hole)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillPath(gear, color)
    painter.end()
    return pixmap
