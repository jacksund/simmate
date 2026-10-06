import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QCheckBox, QComboBox, QStyledItemDelegate

from simmate.desktop import theme
from simmate.desktop.theme import rgba


def input_style() -> str:
    """The stylesheet for inputs, for any widget holding them: rounded, lightly
    bordered inputs that turn teal on hover/focus.

    Combo boxes in it should be `StyledComboBox`es.
    """
    chevron = _icon_file(
        "chevron", (10, 6), [(1, 1), (5, 5), (9, 1)], theme.PRIMARY_COLOR
    )
    check = _icon_file("check", (12, 12), [(2.5, 6.5), (5, 9), (9.5, 3.5)], "white")
    return f"""
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 18px;
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {theme.PRIMARY_COLOR};
}}
/* set the "invalid" property on an input that needs a value (e.g. a missing setting) */
QLineEdit[invalid="true"], QComboBox[invalid="true"] {{
    border-color: {theme.ERROR_COLOR};
}}
/* spin boxes add their own inner margin; match the other inputs' height */
QSpinBox, QDoubleSpinBox {{ padding-top: 3px; padding-bottom: 2px; }}
/* a plain list below the box, rather than a menu panel over it */
QComboBox {{ combobox-popup: 0; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 10px; height: 6px; }}
/* the open dropdown list: rounded, with rows highlighted like the table's */
QComboBoxPrivateContainer {{ border: none; background: transparent; }}
QComboBox QAbstractItemView {{
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    color: palette(text);
    padding: 4px 8px;
    border-radius: 4px;
    min-height: 18px;
}}
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HIGHLIGHT_ALPHA)};
    color: palette(text);
}}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 4px;
}}
QCheckBox::indicator:hover {{ border-color: {theme.PRIMARY_COLOR}; }}
QCheckBox::indicator:checked {{
    background: {theme.PRIMARY_COLOR};
    border-color: {theme.PRIMARY_COLOR};
    image: url("{check}");
}}
"""


class StyledCheckBox(QCheckBox):
    """A check box that shows a pointing hand on hover, like the buttons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class StyledComboBox(QComboBox):
    """A combo box whose dropdown list `input_style()` can round and pad.

    The list sits in its own popup window, which is square and opaque unless made
    frameless and see-through. And the combo's default item delegate ignores
    stylesheets, so swap in a standard one for the `::item` rules to apply.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setItemDelegate(QStyledItemDelegate(self))
        popup = self.view().window()
        popup.setWindowFlags(
            popup.windowFlags()
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def line_pen(color: str) -> QPen:
    """The rounded pen used for small line icons (arrows, check marks, chevrons)."""
    pen = QPen(QColor(color), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def polyline(points: list[tuple[float, float]]) -> QPainterPath:
    """An open path through `points`, for drawing with `line_pen`."""
    path = QPainterPath(QPointF(*points[0]))
    for point in points[1:]:
        path.lineTo(*point)
    return path


def _icon_file(
    name: str, size: tuple[int, int], points: list[tuple[float, float]], color: str
) -> str:
    """Draw a small line icon (e.g. an arrow or check mark) to a PNG.

    Styled inputs drop their native arrows/check marks, and stylesheets can only
    load images from files. Returns the path, ready for `url(...)`.
    """
    path = (
        Path(tempfile.gettempdir()) / f"simmate-desktop-{name}-{color.lstrip('#')}.png"
    )
    if not path.exists():
        scale = 4  # drawn large so it stays crisp on high-DPI screens
        pixmap = QPixmap(size[0] * scale, size[1] * scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale, scale)
        painter.setPen(line_pen(color))
        painter.drawPath(polyline(points))
        painter.end()
        pixmap.save(str(path))
    return path.as_posix()
