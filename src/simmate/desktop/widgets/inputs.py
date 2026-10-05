import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate

from simmate.desktop.widgets.title_bar import PRIMARY_COLOR

# Same teal tint as a hovered table row (see compound_table.HIGHLIGHT_COLOR).
HIGHLIGHT = "rgba(0, 148, 133, 26)"

# Rounded, lightly bordered inputs that turn teal on hover/focus. Fill in the
# image paths with `input_style()`, not by using this directly.
_INPUT_STYLE = f"""
QLineEdit, QComboBox, QDoubleSpinBox {{
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 18px;
}}
QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover,
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
    border-color: {PRIMARY_COLOR};
}}
/* spin boxes add their own inner margin; match the other inputs' height */
QDoubleSpinBox {{ padding-top: 3px; padding-bottom: 2px; }}
/* a plain list below the box, rather than a menu panel over it */
QComboBox {{ combobox-popup: 0; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url("{{chevron}}"); width: 10px; height: 6px; }}
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
    background: {HIGHLIGHT};
    color: palette(text);
}}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 4px;
}}
QCheckBox::indicator:hover {{ border-color: {PRIMARY_COLOR}; }}
QCheckBox::indicator:checked {{
    background: {PRIMARY_COLOR};
    border-color: {PRIMARY_COLOR};
    image: url("{{check}}");
}}
"""


def input_style() -> str:
    """The stylesheet for inputs, for any widget holding them.

    Combo boxes in it also need `style_combo`.
    """
    return _INPUT_STYLE.replace(
        "{chevron}",
        _icon_file("chevron", (10, 6), [(1, 1), (5, 5), (9, 1)], PRIMARY_COLOR),
    ).replace(
        "{check}",
        _icon_file("check", (12, 12), [(2.5, 6.5), (5, 9), (9.5, 3.5)], "white"),
    )


def style_combo(combo: QComboBox):
    """Let `input_style()` round and pad the combo's dropdown list.

    The list sits in its own popup window, which is square and opaque unless made
    frameless and see-through. And the combo's default item delegate ignores
    stylesheets, so swap in a standard one for the `::item` rules to apply.
    """
    combo.setCursor(Qt.CursorShape.PointingHandCursor)
    combo.setItemDelegate(QStyledItemDelegate(combo))
    popup = combo.view().window()
    popup.setWindowFlags(
        popup.windowFlags()
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.NoDropShadowWindowHint
    )
    popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


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
        pen = QPen(QColor(color), 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        line = QPainterPath(QPointF(*points[0]))
        for point in points[1:]:
            line.lineTo(*point)
        painter.drawPath(line)
        painter.end()
        pixmap.save(str(path))
    return path.as_posix()
