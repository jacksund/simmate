import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QPointF, Qt, Signal
from PySide6.QtWidgets import QGraphicsView

from simmate.desktop import theme

# How far above a short (or empty-looking) bar still counts as hovering it, as a
# fraction of the visible y range, so bars of 1-2 compounds stay easy to hit.
HIT_FLOOR = 0.02


class HistogramPlot(pg.PlotWidget):
    """A histogram of one column, with bins you can hover and click.

    The bin edges span every row, so bins stay put while filters change. Bars count
    the rows passing the filters; the rest can show behind them in grey. Selected rows
    are counted in red on top, and one bin can be outlined (e.g. the bin of a point
    hovered in another plot).

    pyqtgraph's bars have no hover/click of their own, so hits are worked out here
    from the cursor position and reported as signals:

    - `bin_hovered(bin | None)` when the bin under the cursor changes.
    - `bin_clicked(bin, modifiers)` on a left-click on a bar.
    - `background_clicked()` on a plain left-click on empty plot space.
    """

    bin_hovered = Signal(object)
    bin_clicked = Signal(int, object)
    background_clicked = Signal()

    def __init__(self):
        super().__init__(background=None)  # transparent: the window shows through
        self.showGrid(x=True, y=True, alpha=0.3)
        # The axes draw the grid lines, over the bars by default; put them behind so
        # the bars stay solid (the view box has no background, so the axes still show).
        for name in ("left", "bottom"):
            self.getPlotItem().getAxis(name).setZValue(-1)
        self.setLabel("left", "Count")
        # see DashboardTab: partial repaints can leave old bars on screen
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view_box = self.getPlotItem().getViewBox()
        self.view_box.setLimits(yMin=0)

        # By row index: each row's bin, whether it passes the filters, and selection.
        self.bin_of_row = np.zeros(0, dtype=int)
        self.passing = np.zeros(0, dtype=bool)
        self.selected = np.zeros(0, dtype=bool)
        self.show_filtered = True
        self.edges = np.array([0.0, 1.0])
        self.heights = np.zeros(1)  # as drawn, for hit-testing
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

    # --- data ---------------------------------------------------------------------------

    def set_values(self, values: np.ndarray, n_bins: int):
        """Re-bin every row by `values` (one per row) into `n_bins` bins."""
        self.edges = np.histogram_bin_edges(values, bins=n_bins)
        # digitize puts the max value past the last edge; keep it in the last bin
        self.bin_of_row = np.clip(np.digitize(values, self.edges) - 1, 0, n_bins - 1)
        if len(self.passing) != len(values):
            self.passing = np.ones(len(values), dtype=bool)
            self.selected = np.zeros(len(values), dtype=bool)
        self.focus_bin = None
        self._set_hovered(None)  # its bar may have moved out from under the cursor
        self._redraw()

    def set_passing(self, passing: np.ndarray, show_filtered: bool):
        """Count only the `passing` rows, with the others in grey if `show_filtered`."""
        self.passing = passing
        self.show_filtered = show_filtered
        self._set_hovered(None)  # its bar may have changed under the cursor
        self._redraw()

    def set_selected(self, rows):
        self.selected = np.zeros(len(self.bin_of_row), dtype=bool)
        self.selected[list(rows)] = True
        self._redraw()

    def set_focus_bin(self, bin: int | None):
        """Outline `bin`, or nothing when None."""
        if bin == self.focus_bin:
            return
        self.focus_bin = bin
        self._draw_focus()

    def rows_in_bin(self, bin: int) -> list[int]:
        """The passing rows in `bin`."""
        return np.flatnonzero((self.bin_of_row == bin) & self.passing).tolist()

    def bin_range(self, bin: int) -> tuple[float, float]:
        return float(self.edges[bin]), float(self.edges[bin + 1])

    # --- drawing ------------------------------------------------------------------------

    def _counts(self, mask: np.ndarray) -> np.ndarray:
        return np.bincount(self.bin_of_row[mask], minlength=len(self.edges) - 1)

    def _redraw(self):
        x0, x1 = self.edges[:-1], self.edges[1:]
        counts = self._counts(self.passing)
        all_counts = self._counts(np.ones_like(self.passing))
        self.heights = all_counts if self.show_filtered else counts
        for item, height, visible in [
            (self.grey_bars, all_counts, self.show_filtered),
            (self.bars, counts, True),
            (self.selected_bars, self._counts(self.selected & self.passing), True),
        ]:
            # empty bins get no bar, else their outline draws along the x axis
            shown = height > 0
            visible = visible and bool(shown.any())
            if visible:
                item.setOpts(x0=x0[shown], x1=x1[shown], height=height[shown])
            item.setVisible(visible)
        self._draw_focus()

    def _draw_focus(self):
        bin = self.focus_bin
        if bin is None:
            self.focus_bar.setVisible(False)
            return
        self.focus_bar.setOpts(
            x0=[self.edges[bin]], x1=[self.edges[bin + 1]], height=[self.heights[bin]]
        )
        self.focus_bar.setVisible(True)

    # --- mouse --------------------------------------------------------------------------

    def bin_at(self, scene_pos: QPointF) -> int | None:
        """The bin of the bar under `scene_pos`, or None."""
        if not self.view_box.sceneBoundingRect().contains(scene_pos):
            return None
        point = self.view_box.mapSceneToView(scene_pos)
        bin = int(np.searchsorted(self.edges, point.x(), side="right")) - 1
        if not 0 <= bin < len(self.heights) or self.heights[bin] == 0:
            return None
        _, (y_min, y_max) = self.view_box.viewRange()
        if point.y() > max(self.heights[bin], HIT_FLOOR * (y_max - y_min)):
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
