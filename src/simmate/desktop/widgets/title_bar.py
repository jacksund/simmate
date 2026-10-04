from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QSizePolicy,
    QToolButton,
    QWidget,
)

# Same teal as the website (see website/core/static/css/simmate.css)
PRIMARY_COLOR = "#009485"
PRIMARY_DARKER = "#006b60"
PRIMARY_LIGHTER = "#00a695"

STYLE = f"""
#titleBar {{ background: {PRIMARY_COLOR}; }}
#titleBar QLabel {{ color: white; font-weight: bold; padding: 0 8px; }}
#titleBar QMenuBar {{ background: transparent; color: white; }}
#titleBar QMenuBar::item {{ background: transparent; padding: 4px 10px; }}
#titleBar QMenuBar::item:selected {{ background: {PRIMARY_LIGHTER}; }}
#titleBar QMenuBar::item:pressed {{ background: {PRIMARY_DARKER}; }}
#titleBar QToolButton {{
    color: white; background: transparent; border: none;
    min-width: 46px; min-height: 32px; font-size: 14px;
}}
#titleBar QToolButton:hover {{ background: {PRIMARY_LIGHTER}; }}
#titleBar QToolButton#closeButton:hover {{ background: #e81123; }}
"""


class TitleBar(QWidget):
    """A custom window title bar in Simmate's primary color.

    The OS draws its own title bar in the system theme (e.g. dark on GNOME), which
    can't be recolored. So the main window hides it and uses this instead. It holds
    the app name, the menu bar, and min/max/close buttons. Drag it to move the
    window, and double-click it to maximize.
    """

    def __init__(self, window: QWidget):
        super().__init__()
        self.window_ = window
        self.setObjectName("titleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(STYLE)

        self.menu_bar = QMenuBar()
        # Menu bars stretch by default, which would cover the bar and block dragging.
        self.menu_bar.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self._drag_offset = None

        minimize_button = QToolButton(text="—")
        minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button = QToolButton(text="☐")
        self.maximize_button.clicked.connect(self.toggle_maximized)
        close_button = QToolButton(text="✕", objectName="closeButton")
        close_button.clicked.connect(window.close)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QLabel("Simmate"))
        layout.addWidget(self.menu_bar, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        for button in [minimize_button, self.maximize_button, close_button]:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            layout.addWidget(button)

    def toggle_maximized(self):
        if self.window_.isMaximized():
            self.window_.showNormal()
        else:
            self.window_.showMaximized()

    def update_maximize_button(self):
        """Call when the window's state changes so the icon reflects it."""
        self.maximize_button.setText("❐" if self.window_.isMaximized() else "☐")

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        # Prefer letting the OS handle the drag, so snapping and multi-monitor
        # moves work. If the platform refuses, move the window ourselves.
        if not self.window_.windowHandle().startSystemMove():
            self._drag_offset = (
                event.globalPosition().toPoint()
                - self.window_.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None:
            self.window_.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximized()
