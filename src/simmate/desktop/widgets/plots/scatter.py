from collections.abc import Callable

import numpy as np
import polars
import pyqtgraph as pg

from simmate.desktop.widgets.plots.base import PlotPanel
from simmate.desktop.widgets.plots.columns import CATEGORY, DATE, NUMBER
from simmate.desktop.widgets.plots.points import PointsLayer
from simmate.desktop.widgets.plots.style import (
    ColorMapping,
    PlotKey,
    category_symbol,
    point_sample,
    sizes,
    style_plot,
    symbols,
)


class ScatterPanel(PlotPanel):
    """A scatter plot of two columns, with points colored, sized and shaped by others.

    Filtered-out points show in grey (or are hidden), selected points are ringed in
    red, and hovering a point shows a card with its structure (both optional, in the
    settings). Log axes leave out points at or below zero.
    """

    display_name = "Scatter"
    title = "Scatter plot"
    description = "Two columns against each other, a point per compound"

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self.column_setting("x", "X axis", (NUMBER, DATE), default="cLogP")
        self.column_setting("y", "Y axis", (NUMBER, DATE), default="pIC50", fallback=1)
        self.column_setting(
            "color", "Color", (NUMBER, CATEGORY), default="pIC50", optional=True
        )
        self.column_setting("size", "Size", (NUMBER,), optional=True)
        self.column_setting("symbol", "Symbol", (CATEGORY,), optional=True)
        self.opacity_setting()
        self.check_setting("log_x", "Log scale X axis", default=False)
        self.check_setting("log_y", "Log scale Y axis", default=False)
        self.check_setting(
            "show_filtered",
            "Show filtered-out points in grey",
            tooltip="Keep compounds excluded by the filters on the plot as grey "
            "points,\ninstead of hiding them",
            on_change=self._redraw,
        )
        self.check_setting(
            "hover_card",
            "Show structure on hover",
            default=svg_of is not None,
            tooltip="Show a small card with the compound's structure beside the "
            "cursor\nwhile hovering a point",
            on_change=lambda: self.points.hide_tooltip(),
        )
        self.settings["hover_card"].setEnabled(svg_of is not None)

        plot = pg.PlotWidget()
        style_plot(plot)
        self._build(plot)
        self.points = PointsLayer(
            self,
            plot,
            describe=lambda point: self.describe_row(
                self.points.rows[point][0], [self.value("x"), self.value("y")]
            ),
            show_card=lambda: self.value("hover_card"),
        )
        self.key = PlotKey(plot)
        self.draw()

    def _xy(self, rows) -> tuple[np.ndarray, np.ndarray]:
        """The rows' plotted x and y (log10'd on log axes, NaN where that can't be)."""
        rows = list(rows)
        coords = []
        for axis in ("x", "y"):
            values = self.columns.numbers(self.value(axis))[rows]
            if self.value(f"log_{axis}"):
                with np.errstate(divide="ignore", invalid="ignore"):
                    values = np.where(values > 0, np.log10(values), np.nan)
            coords.append(values)
        return coords[0], coords[1]

    # --- drawing ------------------------------------------------------------------------

    def _draw(self):
        self.set_axis("bottom", self.value("x"), log=self.value("log_x"))
        self.set_axis("left", self.value("y"), log=self.value("log_y"))
        self.colors = ColorMapping(
            self.columns, self.value("color"), self.value("opacity")
        )
        self.sizes = sizes(self.columns, self.value("size"))
        self.symbols, symbol_labels = symbols(self.columns, self.value("symbol"))
        self.key.show_color_bar(self.colors)
        # categories as colors and/or symbols
        self.key.show_legend(
            [
                (label, point_sample(brush))
                for label, brush in zip(
                    self.colors.labels, self.colors.category_brushes
                )
            ]
            + [
                (label, point_sample(symbol=category_symbol(code)))
                for code, label in enumerate(symbol_labels)
            ]
        )
        self._redraw()
        self.view_box.autoRange()  # emits view_changed via sigRangeChanged

    def _redraw(self):
        shown = np.flatnonzero(self.passing).tolist()
        x, y = self._xy(shown)
        self.points.set_points(
            x,
            y,
            rows=[(row,) for row in shown],
            brushes=[self.colors.brushes[i] for i in shown],
            sizes=self.sizes[shown],
            symbols=[self.symbols[i] for i in shown],
        )
        if self.value("show_filtered"):
            self.points.set_dimmed(*self._xy(np.flatnonzero(~self.passing)))
        else:
            self.points.set_dimmed()

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        self.points.set_selected(rows)

    def show_hovered(self, rows: set[int]):
        self.points.show_hovered(rows)

    def view_ranges(self) -> list[tuple[str, object, object]]:
        if not self._drawable():
            return []
        ranges = []
        for axis, (low, high) in zip(("x", "y"), self.view_box.viewRange()):
            if self.value(f"log_{axis}"):
                low, high = 10**low, 10**high
            ranges.append(self.columns.view_range(self.value(axis), low, high))
        return ranges
