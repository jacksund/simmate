from PySide6.QtCore import QByteArray, QPoint, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QVBoxLayout

TOOLTIP_STYLE = """
#pointTooltip {
    background: palette(base); border: 1px solid palette(mid); border-radius: 6px;
}
"""
CURSOR_OFFSET = 16  # px between the cursor and the card


class PointTooltip(QFrame):
    """A small card (structure + ID) that follows the cursor over a plot's points.

    It floats inside `parent` (e.g. the PlotWidget) and ignores the mouse, so it never
    steals the hover or clicks from the points under it.
    """

    def __init__(self, parent):
        super().__init__(parent, objectName="pointTooltip")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet(TOOLTIP_STYLE)
        shadow = QGraphicsDropShadowEffect(blurRadius=16, offset=QPointF(0, 2))
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        self.title_label = QLabel()
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(180, 135)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self.svg_widget)
        self.hide()

    def show_at(self, svg: bytes, title: str, pos: QPoint):
        """Show `svg` and `title` beside `pos` (in the parent's coordinates)."""
        self.title_label.setText(title)
        self.svg_widget.load(QByteArray(svg))
        # load() swaps in a new renderer config, so re-apply the aspect ratio.
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.adjustSize()

        # below-right of the cursor, flipped to the other side near the edges
        bounds = self.parentWidget().rect()
        x = pos.x() + CURSOR_OFFSET
        if x + self.width() > bounds.right():
            x = pos.x() - CURSOR_OFFSET - self.width()
        y = pos.y() + CURSOR_OFFSET
        if y + self.height() > bounds.bottom():
            y = pos.y() - CURSOR_OFFSET - self.height()
        self.move(max(x, 0), max(y, 0))
        self.show()
        self.raise_()
