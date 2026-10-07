from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from simmate.desktop import theme
from simmate.desktop.theme import rgba


def button_style() -> str:
    """Outlined in the primary color, and filled when on (checked), like the side
    panels' tabs. `filled` buttons are always filled, for a page's main action.
    `muted` buttons are the same in grey, for secondary controls (e.g. plot tools).
    #segmentLeft/#segmentRight join two buttons into one segmented control."""
    return f"""
QPushButton, QToolButton {{
    color: {theme.PRIMARY_COLOR}; background: transparent;
    border: 1px solid {theme.PRIMARY_COLOR}; border-radius: 6px;
    padding: 4px 14px; min-height: 18px;
}}
QToolButton {{ padding: 4px 6px; }}
QPushButton:hover, QToolButton:hover {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HOVER_ALPHA)};
}}
QPushButton:pressed, QToolButton:pressed {{
    background: {rgba(theme.PRIMARY_COLOR, theme.PRESSED_ALPHA)};
}}
QPushButton:checked, QToolButton:checked, QPushButton[filled="true"] {{
    color: white; background: {theme.PRIMARY_COLOR};
}}
QPushButton:checked:hover, QToolButton:checked:hover,
QPushButton[filled="true"]:hover {{ background: {theme.PRIMARY_LIGHTER}; }}
QPushButton:checked:pressed, QToolButton:checked:pressed,
QPushButton[filled="true"]:pressed {{ background: {theme.PRIMARY_DARKER}; }}
QPushButton:disabled, QToolButton:disabled {{
    color: palette(mid); border-color: palette(mid);
}}
QPushButton[filled="true"]:disabled {{ color: white; background: palette(mid); }}
QPushButton[muted="true"], QToolButton[muted="true"] {{
    color: {theme.MUTED_COLOR}; border-color: palette(mid);
}}
QPushButton[muted="true"]:hover, QToolButton[muted="true"]:hover {{
    background: {rgba(theme.MUTED_COLOR, 25)}; border-color: {theme.MUTED_COLOR};
}}
QPushButton[muted="true"]:pressed, QToolButton[muted="true"]:pressed {{
    background: {rgba(theme.MUTED_COLOR, 50)};
}}
QPushButton[muted="true"]:checked, QToolButton[muted="true"]:checked {{
    color: white; background: {theme.MUTED_LIGHTER};
    border-color: {theme.MUTED_LIGHTER};
}}
QPushButton[muted="true"]:checked:hover, QToolButton[muted="true"]:checked:hover {{
    background: {theme.MUTED_LIGHTEST}; border-color: {theme.MUTED_LIGHTEST};
}}
QPushButton[muted="true"]:checked:pressed,
QToolButton[muted="true"]:checked:pressed {{ background: {theme.MUTED_COLOR}; }}
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
        # read by button_style
        self.setProperty("filled", filled)
        self.setProperty("muted", muted)
        self.setStyleSheet(button_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
