from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from simmate.desktop import theme

STYLE = """
#titleBar QLabel { color: white; }
#titleBar #titleLabel { font-weight: bold; padding: 0 12px 0 8px; }
"""


class WindowButton(QAbstractButton):
    """A minimize, maximize, or close button with a thin line-drawn icon.

    The glyph is painted rather than taken from a font, so it looks the same
    (and stays crisp) on every OS. Hovering shows a soft circular highlight, or
    red for the close button.
    """

    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind  # "minimize", "maximize", "restore", or "close"
        self.setFixedSize(QSize(34, 28))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.underMouse():
            if self.kind == "close":
                color = QColor("#c42b1c" if self.isDown() else "#e81123")
            else:
                color = QColor(255, 255, 255, 70 if self.isDown() else 40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            diameter = 24
            circle = QRectF(0, 0, diameter, diameter)
            circle.moveCenter(QRectF(self.rect()).center())
            painter.drawEllipse(circle)

        pen = QPen(QColor("white"), 1.3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        center = QRectF(self.rect()).center()
        size = 9
        box = QRectF(center.x() - size / 2, center.y() - size / 2, size, size)
        if self.kind == "minimize":
            painter.drawLine(box.left(), center.y(), box.right(), center.y())
        elif self.kind == "maximize":
            painter.drawRoundedRect(box, 2, 2)
        elif self.kind == "restore":
            front = box.adjusted(0, 2, -2, 0)
            painter.drawRoundedRect(front, 1.5, 1.5)
            back = QPainterPath()
            back.moveTo(box.left() + 2, box.top())
            back.lineTo(box.right(), box.top())
            back.lineTo(box.right(), box.bottom() - 2)
            painter.drawPath(back)
        elif self.kind == "close":
            painter.drawLine(box.topLeft(), box.bottomRight())
            painter.drawLine(box.topRight(), box.bottomLeft())


class TitleBar(QWidget):
    """A custom window title bar in Simmate's primary color.

    The OS draws its own title bar in the system theme (e.g. dark on GNOME), which
    can't be recolored. So the main window hides it and uses this instead. It holds
    the app icon and name, and min/max/close buttons. Drag it to move
    the window, and double-click it to maximize.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("titleBar")
        self.setStyleSheet(STYLE)
        self.setFixedHeight(40)

        icon = QLabel()
        icon_path = theme.TITLE_ICON_PATH or theme.ICON_PATH
        icon.setPixmap(QIcon(str(icon_path)).pixmap(22, 22))
        title = QLabel(theme.APP_NAME, objectName="titleLabel")

        self._drag_offset = None

        minimize_button = WindowButton("minimize")
        minimize_button.clicked.connect(lambda: self.window().showMinimized())
        self.maximize_button = WindowButton("maximize")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        close_button = WindowButton("close")
        close_button.clicked.connect(lambda: self.window().close())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(2)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addStretch()
        for button in [minimize_button, self.maximize_button, close_button]:
            layout.addWidget(button)

    def paintEvent(self, event):
        # Teal background with rounded top corners (square when maximized, so it
        # meets the screen edges).
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 0 if self.window().isMaximized() else theme.CORNER_RADIUS
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect.adjusted(0, 0, 0, radius), radius, radius)
        painter.setClipRect(rect)
        painter.fillPath(path, QColor(theme.PRIMARY_COLOR))

    def toggle_maximized(self):
        if self.window().isMaximized():
            self.window().showNormal()
        else:
            self.window().showMaximized()

    def update_maximize_button(self):
        """Call when the window's state changes so the icon reflects it."""
        self.maximize_button.kind = (
            "restore" if self.window().isMaximized() else "maximize"
        )
        self.maximize_button.update()
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        # Prefer letting the OS handle the drag, so snapping and multi-monitor
        # moves work. If the platform refuses, move the window ourselves.
        if not self.window().windowHandle().startSystemMove():
            self._drag_offset = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
