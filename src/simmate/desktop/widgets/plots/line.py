from collections.abc import Callable

import numpy as np
import polars
import pyqtgraph as pg
from PySide6.QtCore import Qt

from simmate.desktop import theme
from simmate.desktop.widgets.plots.base import PlotPanel
from simmate.desktop.widgets.plots.columns import CATEGORY, DATE, NUMBER
from simmate.desktop.widgets.plots.points import PointsLayer
from simmate.desktop.widgets.plots.style import PlotKey, category_color, style_plot

# How the y values of rows sharing an x are combined into one point.
AGGREGATES = {
    "None": None,  # a point per compound
    "Mean": polars.col("y").mean(),
    "Median": polars.col("y").median(),
    "Count": polars.col("y").len(),
    "Sum": polars.col("y").sum(),
    "Min": polars.col("y").min(),
    "Max": polars.col("y").max(),
}


class LinePanel(PlotPanel):
    """A line through one column against another (e.g. pIC50 over time), optionally
    a line per category and/or a point per x combining its compounds (e.g. the mean).

    Points hover and click like a scatter plot's; a combined point stands for all of
    its compounds.
    """

    display_name = "Line"
    title = "Line plot"
    description = "One column against another, joined up in order (e.g. over time)"

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self.column_setting("x", "X axis", (NUMBER, DATE), default="tested")
        self.column_setting("y", "Y axis", (NUMBER,), default="pIC50", fallback=1)
        self.choice_setting("aggregate", "Combine each X", list(AGGREGATES), "Mean")
        self.column_setting("group", "Line per", (CATEGORY,), optional=True)
        self.check_setting("markers", "Show markers")
        self.check_setting(
            "show_filtered",
            "Show filtered-out compounds in grey",
            tooltip="Keep compounds excluded by the filters on the plot in grey,\n"
            "instead of hiding them",
            on_change=self._redraw,
        )

        plot = pg.PlotWidget()
        style_plot(plot)
        self._build(plot)
        self.curves: list[pg.PlotCurveItem] = []
        self.points = PointsLayer(self, plot, describe=self._describe)
        self.key = PlotKey(plot)
        self.draw()

    # --- drawing ------------------------------------------------------------------------

    def _draw(self):
        self.set_axis("bottom", self.value("x"))
        aggregate = self.value("aggregate")
        y_label = self.value("y")
        if aggregate == "Count":
            y_label = "Count"
        elif aggregate != "None":
            y_label = f"{aggregate} of {y_label}"
        self.set_axis("left", self.value("y"))
        self.plot.setLabel("left", y_label)
        group = self.value("group")
        self.labels = self.columns.codes(group)[1] if group else [None]
        self.key.show_legend(
            [
                (label, pg.PlotDataItem(pen=pg.mkPen(category_color(code), width=2)))
                for code, label in enumerate(self.labels)
                if label is not None
            ]
        )
        self._redraw()
        self.view_box.autoRange()  # emits view_changed via sigRangeChanged

    def _lines(self, mask: np.ndarray) -> list[tuple[np.ndarray, np.ndarray, list]]:
        """For each line, the x, y and rows of its points, over the rows in `mask`."""
        x = self.columns.numbers(self.value("x"))
        y = self.columns.numbers(self.value("y"))
        group = self.value("group")
        codes = self.columns.codes(group)[0] if group else np.zeros(len(x), dtype=int)
        aggregate = AGGREGATES[self.value("aggregate")]
        lines = []
        for code in range(len(self.labels)):
            rows = np.flatnonzero(mask & (codes == code) & np.isfinite(x))
            if aggregate is None:
                rows = rows[np.argsort(x[rows], kind="stable")]
                lines.append((x[rows], y[rows], [(r,) for r in rows.tolist()]))
                continue
            points = (
                polars.DataFrame({"x": x[rows], "y": y[rows], "row": rows})
                .group_by("x")
                .agg(aggregate.alias("y"), polars.col("row"))
                .sort("x")
            )
            lines.append(
                (
                    points["x"].to_numpy(),
                    points["y"].cast(polars.Float64).to_numpy(),
                    [tuple(r) for r in points["row"].to_list()],
                )
            )
        return lines

    def _redraw(self):
        for curve in self.curves:
            self.plot.removeItem(curve)
        self.curves = []
        grouped = self.value("group") is not None
        combined = self.value("aggregate") != "None"

        if self.value("show_filtered") and not self.passing.all():
            if combined:
                # every compound's line, in grey behind the others
                for x, y, _ in self._lines(np.ones_like(self.passing)):
                    self._curve(x, y, pg.mkPen(150, 150, 150, 90, width=2))
                self.points.set_dimmed()
            else:
                x = self.columns.numbers(self.value("x"))[~self.passing]
                y = self.columns.numbers(self.value("y"))[~self.passing]
                self.points.set_dimmed(x, y)
        else:
            self.points.set_dimmed()

        xs, ys, rows, brushes = [], [], [], []
        markers = self.value("markers")
        for code, (x, y, line_rows) in enumerate(self._lines(self.passing)):
            color = category_color(code) if grouped else theme.PRIMARY_COLOR
            self._curve(x, y, pg.mkPen(color, width=2))
            # without markers, points stay (unseen) so they can still be hovered
            brush = pg.mkBrush(color) if markers else pg.mkBrush(0, 0, 0, 0)
            xs.append(x)
            ys.append(y)
            rows += line_rows
            brushes += [brush] * len(x)
        self.points.set_points(
            np.concatenate(xs) if xs else [],
            np.concatenate(ys) if ys else [],
            rows=rows,
            brushes=brushes,
            sizes=np.full(len(rows), 8.0),
        )

    def _curve(self, x, y, pen):
        keep = np.isfinite(x) & np.isfinite(y)
        curve = pg.PlotCurveItem(x[keep], y[keep], pen=pen)
        curve.setZValue(-2)  # under the points and their rings
        curve.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(curve)
        self.curves.append(curve)

    def _describe(self, point: int) -> str:
        rows = self.points.rows[point]
        x_key, y_key = self.value("x"), self.value("y")
        aggregate = self.value("aggregate")
        if aggregate == "None":
            text = self.describe_row(rows[0], [x_key, y_key])
        else:
            value = self.points.y[point]
            label = "count" if aggregate == "Count" else f"{aggregate.lower()} {y_key}"
            text = (
                f"{x_key} {self.columns.format(x_key, self.points.x[point])}: "
                f"{label} {value:.4g} ({len(rows)} compound(s))"
            )
        group = self.value("group")
        if group is None:
            return text
        line = self.labels[self.columns.codes(group)[0][rows[0]]]
        return f"{group} {line}: {text}"

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        self.points.set_selected(rows)

    def show_hovered(self, rows: set[int]):
        self.points.show_hovered(rows)

    def view_ranges(self) -> list[tuple[str, object, object]]:
        if not self._drawable():
            return []
        (x_low, x_high), (y_low, y_high) = self.view_box.viewRange()
        ranges = [self.columns.view_range(self.value("x"), x_low, x_high)]
        if self.value("aggregate") == "None":  # else y isn't any compound's value
            ranges.append(self.columns.view_range(self.value("y"), y_low, y_high))
        return ranges
