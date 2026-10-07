import numpy as np
import pyqtgraph as pg
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QGraphicsView

from simmate.desktop import theme
from simmate.desktop.widgets.plots.columns import CATEGORY, DataColumns

# One color per category, in order. Red is left out: it marks selected rows.
PALETTE = [
    theme.PRIMARY_COLOR,
    "#e8710a",
    "#1a73e8",
    "#9334e6",
    "#f9ab00",
    "#12b5cb",
    "#e52592",
    "#7cb342",
    "#795548",
    "#5f6368",
]
SYMBOLS = ["o", "s", "t", "d", "+", "x", "star", "h", "p", "t1"]

POINT_SIZE = 10
MIN_POINT_SIZE, MAX_POINT_SIZE = 6, 20


def style_plot(plot: pg.PlotWidget):
    """The look shared by every plot: see-through, with a grid behind the data."""
    plot.setBackground(None)  # transparent: the window shows through
    plot.showGrid(x=True, y=True, alpha=0.3)
    # The axes draw the grid lines, over the data by default; put them behind so bars
    # stay solid (the view box has no background, so the axes still show).
    for name in ("left", "bottom"):
        plot.getPlotItem().getAxis(name).setZValue(-1)
    # Repaint the whole plot on any change. By default only the changed items'
    # bounds are repainted, but pyqtgraph's ScatterPlotItem.setData shrinks those
    # bounds before reporting the change, so points removed outside the new bounds
    # (e.g. hiding the grey points while zoomed in) linger on screen.
    plot.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)


def category_color(code: int, alpha: float = 1.0) -> QColor:
    color = QColor(PALETTE[code % len(PALETTE)])
    color.setAlphaF(alpha)
    return color


class ColorMapping:
    """The color of each row by one column (plotly's `color=`), and its key.

    A number column runs through viridis, keyed by a color bar; a category column
    gets a color per category, keyed by a legend; with no column every row is the
    primary color.
    """

    def __init__(self, columns: DataColumns, key: str | None, alpha: float = 1.0):
        self.key = key
        self.kind = columns.kinds.get(key) if key else None
        self.labels: list[str] = []  # the categories, for a category column
        self.category_brushes: list = []  # and the brush of each
        self.range = (0.0, 1.0)
        self.colormap = pg.colormap.get("viridis")
        n = columns.df.height
        if self.kind == CATEGORY:
            self.codes, self.labels = columns.codes(key)
            colors = [category_color(c, alpha) for c in range(len(self.labels))]
            self.category_brushes = [pg.mkBrush(c) for c in colors]
            self.brushes = [self.category_brushes[c] for c in self.codes]
        elif self.kind:
            values = columns.numbers(key)
            low, high = np.nanmin(values), np.nanmax(values)
            self.range = (float(low), float(high))
            scaled = (values - low) / ((high - low) or 1)
            colors = self.colormap.map(np.nan_to_num(scaled), mode="qcolor")
            for color in colors:
                color.setAlphaF(alpha)
            self.brushes = [pg.mkBrush(c) for c in colors]
        else:
            color = QColor(theme.PRIMARY_COLOR)
            color.setAlphaF(alpha)
            self.brushes = [pg.mkBrush(color)] * n


def sizes(columns: DataColumns, key: str | None) -> np.ndarray:
    """Each row's point size by a number column (plotly's `size=`)."""
    if not key:
        return np.full(columns.df.height, POINT_SIZE, dtype=float)
    values = columns.numbers(key)
    low, high = np.nanmin(values), np.nanmax(values)
    scaled = np.nan_to_num((values - low) / ((high - low) or 1))
    return MIN_POINT_SIZE + scaled * (MAX_POINT_SIZE - MIN_POINT_SIZE)


def category_symbol(code: int) -> str:
    return SYMBOLS[code % len(SYMBOLS)]


def symbols(columns: DataColumns, key: str | None) -> tuple[list[str], list[str]]:
    """Each row's point symbol by a category column (plotly's `symbol=`), and the
    category labels in order."""
    if not key:
        return ["o"] * columns.df.height, []
    codes, labels = columns.codes(key)
    return [category_symbol(c) for c in codes], labels


class PlotKey:
    """The color bar and/or legend beside a plot, redone each time its mappings change."""

    def __init__(self, plot: pg.PlotWidget):
        self.plot_item = plot.getPlotItem()
        self.color_bar: pg.ColorBarItem | None = None
        text = QApplication.palette().text().color()
        base = QApplication.palette().base().color()
        base.setAlpha(200)
        self.legend = pg.LegendItem(
            offset=(-10, 10),
            labelTextColor=text,
            brush=pg.mkBrush(base),
            pen=pg.mkPen(QApplication.palette().mid().color()),
        )
        self.legend.setParentItem(self.plot_item.getViewBox())
        self.legend.hide()

    def show_color_bar(self, mapping: ColorMapping | None):
        """A color bar for a number column's `mapping`, or none."""
        if self.color_bar is not None:
            self.plot_item.layout.removeItem(self.color_bar)
            self.color_bar.scene().removeItem(self.color_bar)
            self.color_bar = None
        if mapping is None or mapping.kind in (None, CATEGORY):
            return
        self.color_bar = pg.ColorBarItem(
            values=mapping.range,
            colorMap=mapping.colormap,
            label=mapping.key,
            interactive=False,
        )
        self.plot_item.layout.addItem(self.color_bar, 2, 5)

    def show_legend(self, entries: list[tuple[str, pg.GraphicsObject]]):
        """A legend of (label, sample item) entries, or none when empty."""
        self.legend.clear()
        for label, sample in entries:
            self.legend.addItem(sample, label)
        self.legend.setVisible(bool(entries))


def point_sample(brush=None, symbol: str = "o") -> pg.ScatterPlotItem:
    """A legend sample for points."""
    return pg.ScatterPlotItem(
        size=POINT_SIZE,
        symbol=symbol,
        pen=pg.mkPen(None) if brush else pg.mkPen(theme.MUTED_COLOR),
        brush=brush or pg.mkBrush(None),
    )
