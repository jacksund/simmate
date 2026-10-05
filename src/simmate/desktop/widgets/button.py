from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from simmate.desktop.theme import (
    HOVER_ALPHA,
    MUTED_COLOR,
    MUTED_LIGHTER,
    MUTED_LIGHTEST,
    PRESSED_ALPHA,
    PRIMARY_COLOR,
    PRIMARY_DARKER,
    PRIMARY_LIGHTER,
    rgba,
)

# Outlined in the primary color, and filled when on (checked), like the side
# panels' tabs. `filled` buttons are always filled, for a page's main action.
# `muted` buttons are the same in grey, for secondary controls (e.g. plot tools).
# #segmentLeft/#segmentRight join two buttons into one segmented control.
BUTTON_STYLE = f"""
QPushButton, QToolButton {{
    color: {PRIMARY_COLOR}; background: transparent;
    border: 1px solid {PRIMARY_COLOR}; border-radius: 6px;
    padding: 4px 14px; min-height: 18px;
}}
QToolButton {{ padding: 4px 6px; }}
QPushButton:hover, QToolButton:hover {{ background: {rgba(PRIMARY_COLOR, HOVER_ALPHA)}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {rgba(PRIMARY_COLOR, PRESSED_ALPHA)}; }}
QPushButton:checked, QToolButton:checked, QPushButton[filled="true"] {{
    color: white; background: {PRIMARY_COLOR};
}}
QPushButton:checked:hover, QToolButton:checked:hover,
QPushButton[filled="true"]:hover {{ background: {PRIMARY_LIGHTER}; }}
QPushButton:checked:pressed, QToolButton:checked:pressed,
QPushButton[filled="true"]:pressed {{ background: {PRIMARY_DARKER}; }}
QPushButton:disabled {{ color: palette(mid); border-color: palette(mid); }}
QPushButton[filled="true"]:disabled {{ color: white; background: palette(mid); }}
QPushButton[muted="true"], QToolButton[muted="true"] {{
    color: {MUTED_COLOR}; border-color: palette(mid);
}}
QPushButton[muted="true"]:hover, QToolButton[muted="true"]:hover {{
    background: {rgba(MUTED_COLOR, 25)}; border-color: {MUTED_COLOR};
}}
QPushButton[muted="true"]:pressed, QToolButton[muted="true"]:pressed {{
    background: {rgba(MUTED_COLOR, 50)};
}}
QPushButton[muted="true"]:checked, QToolButton[muted="true"]:checked {{
    color: white; background: {MUTED_LIGHTER}; border-color: {MUTED_LIGHTER};
}}
QPushButton[muted="true"]:checked:hover, QToolButton[muted="true"]:checked:hover {{
    background: {MUTED_LIGHTEST}; border-color: {MUTED_LIGHTEST};
}}
QPushButton[muted="true"]:checked:pressed,
QToolButton[muted="true"]:checked:pressed {{ background: {MUTED_COLOR}; }}
#segmentLeft {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}
#segmentRight {{
    border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none;
}}
"""


class PrimaryButton(QPushButton):
    """A push button in Simmate's style: primary-color outline, or filled.

    `muted` makes it grey instead, for secondary controls.
    """

    def __init__(
        self, text: str = "", filled: bool = False, muted: bool = False, **kwargs
    ):
        super().__init__(text, **kwargs)
        # read by BUTTON_STYLE
        self.setProperty("filled", filled)
        self.setProperty("muted", muted)
        self.setStyleSheet(BUTTON_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
