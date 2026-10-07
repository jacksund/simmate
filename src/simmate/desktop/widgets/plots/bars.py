import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, Qt, Signal

from simmate.desktop import theme
from simmate.desktop.widgets.plots.style import style_plot

# How far past a short (or empty-looking) bar's end still counts as hovering it, as a
# fraction of the visible y range, so bars of 1-2 compounds stay easy to hit.
HIT_FLOOR = 0.02

AGGREGATES = ["Count", "Sum", "Mean", "Min", "Max"]
# Selected rows add up within these, so their bars can be drawn over the others'.
# Other aggregates show the selected rows' value as a red tick instead.
STACKING = ("Count", "Sum")


class GroupedBars(pg.PlotWidget):
    """Bars that each stand for a group of rows, which you can hover and click.

    Every row belongs to a group (a histogram's bin, a bar plot's category), and each
    group has a bar spanning x0 to x1. A bar's height counts its rows, or aggregates
    one of their values (`set_aggregate`). Bars only count the rows passing the
    filters; with `show_filtered`, bars of every row show behind them in grey.
    Selected rows are counted in red on top, and one bar can be outlined (e.g. the
    bar of a point hovered in another plot).

    pyqtgraph's bars have no hover/click of their own, so hits are worked out here
    from the cursor position and reported as signals:

    - `bin_hovered(bin | None)` when the bar under the cursor changes.
    - `bin_clicked(bin, modifiers)` on a left-click on a bar.
    - `background_clicked()` on a plain left-click on empty plot space.
    """

    bin_hovered = Signal(object)
    bin_clicked = Signal(int, object)
    background_clicked = Signal()

    def __init__(self):
        super().__init__(background=None)
        style_plot(self)
        self.view_box = self.getPlotItem().getViewBox()

        # By row index: each row's group, whether it passes the filters, and selection.
        self.group_of_row = np.zeros(0, dtype=int)
        self.passing = np.zeros(0, dtype=bool)
        self.selected = np.zeros(0, dtype=bool)
        self.show_filtered = True
        # By group: where its bar spans.
        self.x0, self.x1 = np.zeros(1), np.ones(1)
        # How heights are worked out (see `set_aggregate`).
        self.aggregate = "Count"
        self.values: np.ndarray | None = None
        self.percent = False
        self.cumulative = False
        self.heights = np.zeros(1)  # as drawn, for hit-testing
        self.passing_heights = np.zeros(1)  # of the passing rows' bars
        self.hovered: int | None = None
        self.focus_bin: int | None = None

        self.grey_bars = self._bars(
            pen=pg.mkPen(None), brush=pg.mkBrush(150, 150, 150, 60)
        )
        self.bars = self._bars(
            pen=pg.mkPen(theme.PRIMARY_DARKER),
            brush=pg.mkBrush(theme.PRIMARY_COLOR),
        )
        self.selected_bars = self._bars(
            pen=pg.mkPen("#ff5252", width=2.5), brush=pg.mkBrush("#ff8a8a")
        )
        self.focus_bar = self._bars(pen=pg.mkPen("k", width=2), brush=None)

        self.scene().sigMouseMoved.connect(self._on_mouse_moved)
        self.scene().sigMouseClicked.connect(self._on_click)
        self.viewport().installEventFilter(self)  # to notice the mouse leaving

    def _bars(self, pen, brush) -> pg.BarGraphItem:
        item = pg.BarGraphItem(x0=[0], x1=[1], height=[0], pen=pen, brush=brush)
        item.setVisible(False)
        self.addItem(item)
        return item

    @property
    def n_groups(self) -> int:
        return len(self.x0)

    # --- data ---------------------------------------------------------------------------

    def set_groups(self, group_of_row: np.ndarray, x0: np.ndarray, x1: np.ndarray):
        """Put each row in a group (one per row), and each group's bar at x0 to x1."""
        self.group_of_row = np.asarray(group_of_row, dtype=int)
        self.x0, self.x1 = np.asarray(x0, dtype=float), np.asarray(x1, dtype=float)
        if len(self.passing) != len(self.group_of_row):
            self.passing = np.ones(len(self.group_of_row), dtype=bool)
            self.selected = np.zeros(len(self.group_of_row), dtype=bool)
        self.focus_bin = None
        self._set_hovered(None)  # its bar may have moved out from under the cursor
        self._redraw()

    def set_aggregate(
        self,
        aggregate: str = "Count",
        values: np.ndarray | None = None,
        percent: bool = False,
        cumulative: bool = False,
    ):
        """How heights are worked out: `aggregate` (one of `AGGREGATES`) of `values`
        (one per row; unused for "Count") over each group's rows. Counts and sums can
        be shown as a `percent` of the total, and/or added up over the groups so far
        (`cumulative`; hovering a bar then gives every row up to it)."""
        stacking = aggregate in STACKING
        self.aggregate = aggregate
        self.values = values
        self.percent = percent and stacking
        self.cumulative = cumulative and stacking
        # Counts are never negative, so the view stops at 0; values can be.
        self.view_box.setLimits(yMin=0 if aggregate == "Count" else None)
        self._redraw()

    def set_passing(self, passing: np.ndarray, show_filtered: bool):
        """Count only the `passing` rows, with the others in grey if `show_filtered`."""
        self.passing = passing
        self.show_filtered = show_filtered
        self._set_hovered(None)  # its bar may have changed under the cursor
        self._redraw()

    def set_selected(self, rows):
        self.selected = np.zeros(len(self.group_of_row), dtype=bool)
        self.selected[list(rows)] = True
        self._redraw()

    def set_focus_bin(self, bin: int | None):
        """Outline `bin`, or nothing when None."""
        if bin == self.focus_bin:
            return
        self.focus_bin = bin
        self._draw_focus()

    def bin_of(self, row: int) -> int:
        return int(self.group_of_row[row])

    def rows_in_bin(self, bin: int) -> list[int]:
        """The passing rows in `bin` (or in it and every one before, if cumulative)."""
        in_bin = (
            self.group_of_row <= bin if self.cumulative else self.group_of_row == bin
        )
        return np.flatnonzero(in_bin & self.passing).tolist()

    # --- drawing ------------------------------------------------------------------------

    def _aggregated(self, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Each group's height and row count, over the rows in `mask`."""
        n = self.n_groups
        groups = self.group_of_row[mask]
        counts = np.bincount(groups, minlength=n).astype(float)
        if self.aggregate == "Count" or self.values is None:
            return counts, counts
        values = np.nan_to_num(self.values[mask])
        sums = np.bincount(groups, weights=values, minlength=n)
        if self.aggregate == "Sum":
            heights = sums
        elif self.aggregate == "Mean":
            heights = np.divide(sums, counts, out=np.zeros(n), where=counts > 0)
        else:
            extreme = np.minimum if self.aggregate == "Min" else np.maximum
            heights = np.full(n, np.inf if self.aggregate == "Min" else -np.inf)
            extreme.at(heights, groups, values)
            heights[counts == 0] = 0
        return heights, counts

    def _heights(self, mask: np.ndarray, total: float) -> tuple[np.ndarray, np.ndarray]:
        heights, counts = self._aggregated(mask)
        if self.cumulative:
            heights, counts = np.cumsum(heights), np.cumsum(counts)
        if self.percent:
            heights = heights / (total or 1) * 100
        return heights, counts

    def _redraw(self):
        # percents are of the passing rows' total, so all bars share one scale
        total = self._aggregated(self.passing)[0].sum()
        passing, passing_counts = self._heights(self.passing, total)
        every, every_counts = self._heights(np.ones_like(self.passing), total)
        selected, selected_counts = self._heights(self.selected & self.passing, total)
        self.passing_heights = passing
        # hit-test (and outline) whichever bar reaches furthest
        self.heights = passing
        if self.show_filtered:
            self.heights = np.where(np.abs(every) > np.abs(passing), every, passing)
        stacking = self.aggregate in STACKING
        for item, height, counts, visible in [
            (self.grey_bars, every, every_counts, self.show_filtered),
            (self.bars, passing, passing_counts, True),
            (self.selected_bars, selected, selected_counts, True),
        ]:
            # empty groups get no bar, else their outline draws along the x axis
            shown = counts > 0
            visible = visible and bool(shown.any())
            if visible:
                x0, x1 = self.x0[shown], self.x1[shown]
                if item is self.selected_bars and not stacking:
                    # a tick at the selected rows' value (they don't add up to a bar)
                    item.setOpts(x0=x0, x1=x1, y0=height[shown], height=0)
                else:
                    item.setOpts(x0=x0, x1=x1, y0=0, height=height[shown])
            item.setVisible(visible)
        self._draw_focus()

    def _draw_focus(self):
        bin = self.focus_bin
        if bin is None or bin >= self.n_groups:
            self.focus_bar.setVisible(False)
            return
        self.focus_bar.setOpts(
            x0=[self.x0[bin]], x1=[self.x1[bin]], height=[self.heights[bin]]
        )
        self.focus_bar.setVisible(True)

    # --- mouse --------------------------------------------------------------------------

    def bin_at(self, scene_pos: QPointF) -> int | None:
        """The group of the bar under `scene_pos`, or None."""
        if not self.view_box.sceneBoundingRect().contains(scene_pos):
            return None
        point = self.view_box.mapSceneToView(scene_pos)
        hits = np.flatnonzero((self.x0 <= point.x()) & (point.x() < self.x1))
        if len(hits) == 0 or self.heights[hits[0]] == 0:
            return None
        bin = int(hits[0])
        _, (y_min, y_max) = self.view_box.viewRange()
        floor = HIT_FLOOR * (y_max - y_min)
        height = self.heights[bin]
        low, high = min(0, height) - floor, max(0, height) + floor
        if not low <= point.y() <= high:
            return None
        return bin

    def _set_hovered(self, bin: int | None):
        if bin != self.hovered:
            self.hovered = bin
            self.bin_hovered.emit(bin)

    def _on_mouse_moved(self, scene_pos):
        self._set_hovered(self.bin_at(scene_pos))

    def _on_click(self, event):
        # Like the scatter plot: Ctrl+click on empty space keeps the selection, and a
        # double-click is left to reset the view.
        if (
            event.button() != Qt.MouseButton.LeftButton
            or event.isAccepted()
            or event.double()
        ):
            return
        bin = self.bin_at(event.scenePos())
        if bin is not None:
            self.bin_clicked.emit(bin, event.modifiers())
        elif not (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ) and self.view_box.sceneBoundingRect().contains(event.scenePos()):
            self.background_clicked.emit()

    def eventFilter(self, watched, event):
        if watched is self.viewport() and event.type() == QEvent.Type.Leave:
            self._set_hovered(None)
        return False


class HistogramPlot(GroupedBars):
    """A histogram of one column: `GroupedBars` with a group per bin of its values.

    The bin edges span every row, so bins stay put while filters change.
    """

    def __init__(self):
        super().__init__()
        self.edges = np.array([0.0, 1.0])
        self.setLabel("left", "Count")

    def set_values(self, values: np.ndarray, n_bins: int):
        """Re-bin every row by `values` (one per row) into `n_bins` bins."""
        finite = values[np.isfinite(values)]
        self.edges = np.histogram_bin_edges(
            finite if len(finite) else [0.0, 1.0], bins=n_bins
        )
        # digitize puts the max value past the last edge; keep it in the last bin
        # (and rows with no value land in the first or last bin)
        groups = np.clip(
            np.digitize(np.nan_to_num(values), self.edges) - 1, 0, n_bins - 1
        )
        self.set_groups(groups, self.edges[:-1], self.edges[1:])

    def bin_range(self, bin: int) -> tuple[float, float]:
        return float(self.edges[bin]), float(self.edges[bin + 1])
