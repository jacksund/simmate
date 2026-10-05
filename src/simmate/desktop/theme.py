# -*- coding: utf-8 -*-

"""
Colors and other look-and-feel constants shared by every part of the desktop app.
"""

from pathlib import Path

from PySide6.QtGui import QColor

import simmate

# Same teal as the website (see website/core/static/css/simmate.css)
PRIMARY_COLOR = "#009485"
PRIMARY_DARKER = "#006b60"
PRIMARY_LIGHTER = "#00a695"
# Grey for secondary text and controls (e.g. unselected tabs), plus lighter
# shades for the fill of a checked grey button (and its hover).
MUTED_COLOR = "#5f6368"
MUTED_LIGHTER = "#80868b"
MUTED_LIGHTEST = "#9aa0a6"

# Radius (px) of the window's rounded corners.
CORNER_RADIUS = 10

# Alphas (0-255) of the primary-color tints shared across widgets: a hovered row
# or list item, and a hovered/pressed outlined button (also the header tint).
HIGHLIGHT_ALPHA = 26
HOVER_ALPHA = 30
PRESSED_ALPHA = 60

ICON_PATH = (
    Path(simmate.__file__).parent / "website/core/static/images/simmate-icon.svg"
)


def tint(color: str, alpha: int) -> QColor:
    """`color` (e.g. "#009485") made see-through, with `alpha` from 0 to 255."""
    tinted = QColor(color)
    tinted.setAlpha(alpha)
    return tinted


def rgba(color: str, alpha: int | str) -> str:
    """`color` as a stylesheet rgba(), with `alpha` from 0 to 255 (or e.g. "25%")."""
    red, green, blue, _ = QColor(color).getRgb()
    return f"rgba({red}, {green}, {blue}, {alpha})"
