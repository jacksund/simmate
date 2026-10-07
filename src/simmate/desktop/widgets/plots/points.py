from collections.abc import Callable

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt

from simmate.desktop.widgets.plots.style import POINT_SIZE
from simmate.desktop.widgets.point_tooltip import PointTooltip

SELECTED_RING = 9  # px wider than its point
HOVER_RING = 14  # around a single hovered point
GROUP_HOVER_RING = 6  # around each of a group of hovered points (e.g. a bin's)


class PointsLayer:
    """Points on a plot that stand for rows, with the dashboard's hover/click behavior.

    Each point stands for one or more rows (e.g. a line plot's average of the rows at
    one x). Hovering a point reports its rows and shows a card with the compound when
    it's one row; clicking reports them; clicking empty plot space reports that.
    Points of rows hovered or selected elsewhere are ringed, and filtered-out rows can
    show as grey points (`set_dimmed`), under everything so they never take the mouse.

    It reports through the `panel`'s signals (see `PlotPanel`), and asks it for
    `describe(point)` (the status bar text) and `show_card()` (whether to show the card).
    """

    def __init__(
        self,
        panel,
        plot: pg.PlotWidget,
        describe: Callable[[int], str],
        show_card: Callable[[], bool] = lambda: False,
    ):
        self.panel = panel
        self.plot = plot
        self.view_box = plot.getPlotItem().getViewBox()
        self.describe = describe
        self.show_card = show_card
        n_rows = panel.df.height
        # by point: x, y, size, and the rows it stands for
        self.x = self.y = self.sizes = np.zeros(0)
        self.rows: list[tuple[int, ...]] = []
        self.point_of_row = np.full(n_rows, -1)  # by row: its point, or -1
        self.selected_rows: set[int] = set()

        self.scatter = pg.ScatterPlotItem(
            size=POINT_SIZE,
            pen=pg.mkPen(None),
            hoverable=True,
            hoverPen=pg.mkPen("k", width=2),
            tip=None,  # the hover card replaces a text tooltip
        )
        self.scatter.sigHovered.connect(self._on_hover)
        self.scatter.sigClicked.connect(self._on_click)
        # after the points get the click, so we can tell when none was hit
        plot.scene().sigMouseClicked.connect(self._on_background_click)
        self.tooltip = PointTooltip(plot)
        # its point moves out from under it
        self.view_box.sigRangeChanged.connect(lambda *_: self.tooltip.hide())

        # Overlays drawn under the data points so they never steal hovers or clicks.
        self.dimmed = self._overlay(
            size=8, pen=pg.mkPen(None), brush=pg.mkBrush(150, 150, 150, 60)
        )
        self.selection_marks = self._overlay(
            size=POINT_SIZE + SELECTED_RING, pen=pg.mkPen("#ff5252", width=2.5)
        )
        # rings points hovered elsewhere (a table row, or a histogram bin's points)
        self.hover_marks = self._overlay(
            size=POINT_SIZE + HOVER_RING, pen=pg.mkPen("k", width=2)
        )
        plot.addItem(self.scatter)

    def _overlay(self, size, pen, brush=None) -> pg.ScatterPlotItem:
        item = pg.ScatterPlotItem(size=size, pen=pen, brush=brush or pg.mkBrush(None))
        item.setZValue(-1)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(item)
        return item

    # --- data ---------------------------------------------------------------------------

    def set_points(
        self,
        x: np.ndarray,
        y: np.ndarray,
        rows: list[tuple[int, ...]],
        brushes: list,
        sizes: np.ndarray | None = None,
        symbols: list[str] | None = None,
    ):
        """Draw a point at each (x, y) for the `rows` it stands for. Points with a
        missing (NaN) coordinate are left out."""
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        sizes = np.full(len(x), POINT_SIZE, dtype=float) if sizes is None else sizes
        symbols = ["o"] * len(x) if symbols is None else symbols
        keep = np.flatnonzero(np.isfinite(x) & np.isfinite(y))
        self.x, self.y, self.sizes = x[keep], y[keep], np.asarray(sizes)[keep]
        self.rows = [rows[i] for i in keep]
        self.point_of_row[:] = -1
        for point, point_rows in enumerate(self.rows):
            self.point_of_row[list(point_rows)] = point
        varied = bool(len(self.sizes)) and np.ptp(self.sizes) > 0
        self.scatter.setData(
            x=self.x,
            y=self.y,
            brush=[brushes[i] for i in keep],
            size=self.sizes,
            symbol=[symbols[i] for i in keep],
            data=list(range(len(keep))),
            # grow a hovered point, unless sizes already mean something
            hoverSize=-1 if varied else 16,
        )
        self._draw_selection()
        self.show_hovered(set())
        self.tooltip.hide()

    def set_dimmed(self, x: np.ndarray | None = None, y: np.ndarray | None = None):
        """Grey points (e.g. the filtered-out rows), or none."""
        if x is None:
            # Not .clear(): it skips prepareGeometryChange, so Qt never repaints the
            # area the old points covered and they linger on screen.
            self.dimmed.setData(x=[], y=[])
        else:
            self.dimmed.setData(x=x, y=y)

    def set_selected(self, rows: set[int]):
        self.selected_rows = set(rows)
        self._draw_selection()

    def _points_of(self, rows) -> np.ndarray:
        points = self.point_of_row[list(rows)] if rows else np.zeros(0, dtype=int)
        return np.unique(points[points >= 0])

    def _draw_selection(self):
        points = self._points_of(self.selected_rows)
        self.selection_marks.setData(
            x=self.x[points], y=self.y[points], size=self.sizes[points] + SELECTED_RING
        )

    def show_hovered(self, rows: set[int]):
        """Ring the points of `rows`, hovered elsewhere (none when empty)."""
        points = self._points_of(rows)
        # a smaller ring for a group of points (e.g. a histogram bin's)
        ring = HOVER_RING if len(rows) == 1 else GROUP_HOVER_RING
        self.hover_marks.setData(
            x=self.x[points], y=self.y[points], size=self.sizes[points] + ring
        )

    # --- mouse --------------------------------------------------------------------------

    def _nearest(self, points, event) -> int | None:
        """Of the (possibly overlapping) points under the cursor, the one closest on screen."""
        if len(points) == 0:
            return None
        cursor = event.scenePos()

        def distance(point):
            delta = self.view_box.mapViewToScene(point.pos()) - cursor
            return delta.x() ** 2 + delta.y() ** 2

        return min(points, key=distance).data()

    def _on_hover(self, _item, points, event):
        point = self._nearest(points, event)
        self.panel.rows_hovered.emit(set() if point is None else set(self.rows[point]))
        if point is None:
            self.tooltip.hide()
            return
        rows = self.rows[point]
        if len(rows) == 1 and self.show_card() and self.panel.svg_of is not None:
            self.tooltip.show_at(
                self.panel.svg_of(rows[0]),
                self.panel.df["id"][rows[0]],
                self.plot.mapFromScene(event.scenePos()),
            )
        else:
            self.tooltip.hide()
        self.panel.status.emit(self.describe(point))

    def _on_click(self, _item, points, event):
        point = self._nearest(points, event)
        if point is not None:
            rows = self.rows[point]
            clicked = rows[0] if len(rows) == 1 else None
            self.panel.rows_clicked.emit(set(rows), event.modifiers(), clicked)
        event.accept()

    def _on_background_click(self, event):
        # A click that no point accepted, inside the plot area (not on an axis or
        # the color bar), clears the selection. Ctrl+click there keeps it, and a
        # double-click is left to reset the view.
        if (
            event.button() != Qt.MouseButton.LeftButton
            or event.isAccepted()
            or event.double()
            or event.modifiers() & Qt.KeyboardModifier.ControlModifier
            or not self.view_box.sceneBoundingRect().contains(event.scenePos())
        ):
            return
        self.panel.background_clicked.emit()

    def hide_tooltip(self):
        self.tooltip.hide()
