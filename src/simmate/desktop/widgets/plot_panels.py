from collections.abc import Callable

import numpy as np
import polars
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import NUMERIC_COLUMNS
from simmate.desktop.widgets.histogram import HistogramPlot
from simmate.desktop.widgets.inputs import StyledCheckBox, StyledComboBox, input_style
from simmate.desktop.widgets.plot_toolbar import ResetViewButton, SettingsButton
from simmate.desktop.widgets.point_tooltip import PointTooltip


class PlotPanel(QWidget):
    """One plot of the dashboard's rows, with its toolbar and settings above it.

    Each type of plot subclasses this. Plots know nothing about each other or the
    table: they report what the user does through signals, and the dashboard tells
    every plot what to show through the `set_*`/`show_hovered` methods.

    - `rows_hovered(rows)`: the rows under the cursor changed (empty once off them).
    - `rows_clicked(rows, modifiers, row)`: rows were clicked; `row` is the one
      clicked on, if it was a single row (else None).
    - `background_clicked()`: a plain click on empty plot space.
    - `view_changed()`: the plot was zoomed or panned.
    - `status(text)`: a message for the status bar.
    """

    title = "Plot"

    rows_hovered = Signal(object)
    rows_clicked = Signal(object, object, object)
    background_clicked = Signal()
    view_changed = Signal()
    status = Signal(str)

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__()
        self.df = df
        # how a row's compound is drawn, e.g. for a card on hover
        self.svg_of = svg_of
        # By row index: which rows pass the filters.
        self.passing = np.ones(df.height, dtype=bool)
        self.selected_rows: set[int] = set()

    def _build(self, plot: pg.PlotWidget, settings: list):
        """Lay out `plot` under its toolbar. `settings` are the rows of its settings
        panel: (label, input) pairs, or a widget (e.g. a checkbox) on its own."""
        self.plot = plot
        self.view_box = plot.getPlotItem().getViewBox()
        self.view_box.sigRangeChanged.connect(lambda *_: self.view_changed.emit())

        settings_panel = QWidget()
        settings_panel.setStyleSheet(input_style())  # same inputs as the filters
        settings_layout = QFormLayout(settings_panel)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(10)
        for row in settings:
            if isinstance(row, tuple):
                settings_layout.addRow(*row)
            else:
                settings_layout.addRow(row)

        controls = QHBoxLayout()
        controls.setSpacing(2)  # the two buttons sit close together
        controls.addStretch()
        controls.addWidget(ResetViewButton(plot))
        controls.addWidget(
            SettingsButton(settings_panel, tooltip=f"{self.title} settings")
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)  # between the buttons and the plot, as for the table
        layout.addLayout(controls)
        layout.addWidget(plot, stretch=1)

    def set_mouse_mode(self, mode: int):
        """Whether left-drag zooms (`pg.ViewBox.RectMode`) or pans (`PanMode`)."""
        self.view_box.setMouseMode(mode)

    def set_passing(self, passing: np.ndarray):
        """Which rows pass the filters (by row index)."""
        self.passing = passing
        self._redraw()

    def set_selected(self, rows: set[int]):
        self.selected_rows = set(rows)

    def show_hovered(self, rows: set[int]):
        """Mark `rows`, hovered somewhere else (e.g. in the table), or none when empty."""

    def view_ranges(self) -> list[tuple[str, float, float]]:
        """The (column, low, high) ranges in view, which the table is narrowed to."""
        return []

    def _redraw(self):
        pass


class ScatterPanel(PlotPanel):
    """A scatter plot of two columns, colored by potency.

    Filtered-out points show in grey (or are hidden), selected points are ringed in
    red, and hovering a point shows a card with its structure (both optional, in the
    settings).
    """

    title = "Scatter plot"

    def __init__(self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None):
        super().__init__(df, svg_of)
        self.x_combo = StyledComboBox()
        self.y_combo = StyledComboBox()
        for combo, default in [(self.x_combo, "cLogP"), (self.y_combo, "pIC50")]:
            combo.addItems(NUMERIC_COLUMNS)
            combo.setCurrentText(default)
            combo.currentTextChanged.connect(self._update_axes)

        self.show_filtered_checkbox = StyledCheckBox("Show filtered-out points in grey")
        self.show_filtered_checkbox.setToolTip(
            "Keep compounds excluded by the filters on the plot as grey points,\n"
            "instead of hiding them"
        )
        self.show_filtered_checkbox.setChecked(True)
        self.show_filtered_checkbox.toggled.connect(self._redraw)

        self.hover_card_checkbox = StyledCheckBox("Show structure on hover")
        self.hover_card_checkbox.setToolTip(
            "Show a small card with the compound's structure beside the cursor\n"
            "while hovering a point"
        )
        self.hover_card_checkbox.setChecked(svg_of is not None)
        self.hover_card_checkbox.setEnabled(svg_of is not None)
        self.hover_card_checkbox.toggled.connect(
            lambda on: on or self.point_tooltip.hide()
        )

        plot = pg.PlotWidget(background=None)  # transparent: the window shows through
        plot.showGrid(x=True, y=True, alpha=0.3)
        # Repaint the whole plot on any change. By default only the changed items'
        # bounds are repainted, but pyqtgraph's ScatterPlotItem.setData shrinks
        # those bounds before reporting the change, so points removed outside the
        # new bounds (e.g. hiding the grey points while zoomed in) linger on screen.
        plot.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._build(
            plot,
            [
                ("X axis", self.x_combo),
                ("Y axis", self.y_combo),
                self.show_filtered_checkbox,
                self.hover_card_checkbox,
            ],
        )

        # Color every point by potency so trends are visible regardless of the chosen axes.
        pic50 = self.df["pIC50"].to_numpy()
        cmap = pg.colormap.get("viridis")
        colors = cmap.map((pic50 - pic50.min()) / np.ptp(pic50), mode="qcolor")
        self.brushes = [pg.mkBrush(c) for c in colors]
        color_bar = pg.ColorBarItem(
            values=(pic50.min(), pic50.max()),
            colorMap=cmap,
            label="pIC50",
            interactive=False,
        )
        plot.getPlotItem().layout.addItem(color_bar, 2, 5)

        self.scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(None),
            hoverable=True,
            hoverSize=16,
            hoverPen=pg.mkPen("k", width=2),
            tip=None,  # the hover card replaces a text tooltip
        )
        self.scatter.sigHovered.connect(self._on_hover)
        self.scatter.sigClicked.connect(self._on_click)
        # after the points get the click, so we can tell when none was hit
        plot.scene().sigMouseClicked.connect(self._on_background_click)
        self.point_tooltip = PointTooltip(plot)
        # its point moves out from under it
        self.view_box.sigRangeChanged.connect(lambda *_: self.point_tooltip.hide())

        # Overlays drawn under the data points so they never steal hovers or clicks.
        self.dimmed_scatter = self._overlay(
            size=8, pen=pg.mkPen(None), brush=pg.mkBrush(150, 150, 150, 60)
        )
        self.selection_marks = self._overlay(
            size=19, pen=pg.mkPen("#ff5252", width=2.5)
        )
        # rings points hovered elsewhere (a table row, or a histogram bin's points)
        self.hover_marks = self._overlay(size=24, pen=pg.mkPen("k", width=2))
        plot.addItem(self.scatter)

        self._update_axes()

    def _overlay(self, size, pen, brush=None) -> pg.ScatterPlotItem:
        item = pg.ScatterPlotItem(size=size, pen=pen, brush=brush or pg.mkBrush(None))
        item.setZValue(-1)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(item)
        return item

    def _xy(self, row_indices) -> tuple[np.ndarray, np.ndarray]:
        row_indices = list(row_indices)
        return (
            self.df[self.x_combo.currentText()].to_numpy()[row_indices],
            self.df[self.y_combo.currentText()].to_numpy()[row_indices],
        )

    def _nearest(self, points, event) -> int | None:
        """Of the (possibly overlapping) points under the cursor, the row closest to it on screen."""
        if len(points) == 0:
            return None
        cursor = event.scenePos()

        def distance(point):
            delta = self.view_box.mapViewToScene(point.pos()) - cursor
            return delta.x() ** 2 + delta.y() ** 2

        return min(points, key=distance).data()

    # --- drawing ------------------------------------------------------------------------

    def _update_axes(self):
        self._redraw()
        self.plot.setLabel("bottom", self.x_combo.currentText())
        self.plot.setLabel("left", self.y_combo.currentText())
        self.view_box.autoRange()  # emits view_changed via sigRangeChanged

    def _redraw(self):
        shown = np.flatnonzero(self.passing).tolist()
        x, y = self._xy(shown)
        self.scatter.setData(
            x=x, y=y, brush=[self.brushes[i] for i in shown], data=shown
        )
        if self.show_filtered_checkbox.isChecked():
            x, y = self._xy(np.flatnonzero(~self.passing))
            self.dimmed_scatter.setData(x=x, y=y)
        else:
            # Not .clear(): it skips prepareGeometryChange, so Qt never repaints the
            # area the old points covered and they linger on screen.
            self.dimmed_scatter.setData(x=[], y=[])
        self._draw_selection()
        self.show_hovered(set())
        self.point_tooltip.hide()

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        self._draw_selection()

    def _draw_selection(self):
        x, y = self._xy(sorted(r for r in self.selected_rows if self.passing[r]))
        self.selection_marks.setData(x=x, y=y)

    def show_hovered(self, rows: set[int]):
        # a smaller ring for a group of points (e.g. a histogram bin's)
        x, y = self._xy(sorted(rows))
        self.hover_marks.setData(x=x, y=y, size=24 if len(rows) == 1 else 16)

    def view_ranges(self) -> list[tuple[str, float, float]]:
        (x_min, x_max), (y_min, y_max) = self.view_box.viewRange()
        return [
            (self.x_combo.currentText(), x_min, x_max),
            (self.y_combo.currentText(), y_min, y_max),
        ]

    # --- mouse --------------------------------------------------------------------------

    def _on_hover(self, _item, points, event):
        row = self._nearest(points, event)
        self.rows_hovered.emit(set() if row is None else {row})
        if row is None:
            self.point_tooltip.hide()
            return
        if self.hover_card_checkbox.isChecked():
            self.point_tooltip.show_at(
                self.svg_of(row),
                self.df["id"][row],
                self.plot.mapFromScene(event.scenePos()),
            )
        self.status.emit(f"{self.df['id'][row]}: pIC50 {self.df['pIC50'][row]}")

    def _on_click(self, _item, points, event):
        clicked = self._nearest(points, event)
        self.rows_clicked.emit({clicked}, event.modifiers(), clicked)
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
        self.background_clicked.emit()


class HistogramPanel(PlotPanel):
    """A histogram of one column, with bins to hover and click (see `HistogramPlot`)."""

    title = "Histogram"

    def __init__(
        self, df: polars.DataFrame, svg_of: Callable[[int], bytes] | None = None
    ):
        super().__init__(df, svg_of)
        self.column_combo = StyledComboBox()
        self.column_combo.addItems(NUMERIC_COLUMNS)
        self.column_combo.setCurrentText("MolWt")
        self.column_combo.currentTextChanged.connect(self._update_histogram)
        self.bins_combo = StyledComboBox()
        self.bins_combo.addItems(["10", "20", "30", "50"])
        self.bins_combo.setCurrentText("20")
        self.bins_combo.currentTextChanged.connect(self._update_histogram)

        self.show_filtered_checkbox = StyledCheckBox(
            "Show filtered-out compounds in grey"
        )
        self.show_filtered_checkbox.setToolTip(
            "Count compounds excluded by the filters in grey bars behind the others,\n"
            "instead of leaving them out"
        )
        self.show_filtered_checkbox.setChecked(True)
        self.show_filtered_checkbox.toggled.connect(self._redraw)

        self.bin_hover_checkbox = StyledCheckBox("Highlight a bin's compounds on hover")
        self.bin_hover_checkbox.setToolTip(
            "While hovering a bar, highlight its compounds' rows and ring\n"
            "their points in the scatter plots"
        )
        self.bin_hover_checkbox.setChecked(True)

        self.histogram = HistogramPlot()
        self.histogram.bin_hovered.connect(self._on_bin_hover)
        self.histogram.bin_clicked.connect(
            lambda bin, modifiers: self.rows_clicked.emit(
                set(self.histogram.rows_in_bin(bin)), modifiers, None
            )
        )
        self.histogram.background_clicked.connect(self.background_clicked)
        self._build(
            self.histogram,
            [
                ("Column", self.column_combo),
                ("Bins", self.bins_combo),
                self.show_filtered_checkbox,
                self.bin_hover_checkbox,
            ],
        )
        self._update_histogram()

    def _update_histogram(self):
        """Re-bin after the column or bin count changed."""
        key = self.column_combo.currentText()
        self.histogram.set_values(
            self.df[key].to_numpy(), int(self.bins_combo.currentText())
        )
        self._redraw()
        self.histogram.setLabel("bottom", key)
        self.view_box.autoRange()  # emits view_changed via sigRangeChanged

    def _redraw(self):
        self.histogram.set_passing(
            self.passing, self.show_filtered_checkbox.isChecked()
        )

    def set_selected(self, rows: set[int]):
        super().set_selected(rows)
        self.histogram.set_selected(rows)

    def show_hovered(self, rows: set[int]):
        # outline the bin of a single hovered compound
        self.histogram.set_focus_bin(
            int(self.histogram.bin_of_row[next(iter(rows))]) if len(rows) == 1 else None
        )

    def view_ranges(self) -> list[tuple[str, float, float]]:
        (low, high), _ = self.view_box.viewRange()
        return [(self.column_combo.currentText(), low, high)]

    def _on_bin_hover(self, bin: int | None):
        self.histogram.set_focus_bin(bin)
        if bin is None:
            self.rows_hovered.emit(set())
            return
        rows = set(self.histogram.rows_in_bin(bin))
        if self.bin_hover_checkbox.isChecked():
            self.rows_hovered.emit(rows)
        low, high = self.histogram.bin_range(bin)
        self.status.emit(
            f"{self.column_combo.currentText()} {low:.4g} to {high:.4g}: "
            f"{len(rows)} compound(s)"
        )


class PlotTypeChooser(QWidget):
    """What a new plot shows until its type is picked: one button per type."""

    chosen = Signal(str)

    def __init__(self, names: list[str]):
        super().__init__()
        label = QLabel("Choose a plot type")
        label.setStyleSheet(f"color: {theme.MUTED_COLOR};")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons = QHBoxLayout()
        buttons.addStretch()
        for name in names:
            button = PrimaryButton(name)
            button.clicked.connect(lambda _=False, name=name: self.chosen.emit(name))
            buttons.addWidget(button)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(8)
        layout.addLayout(buttons)
        layout.addStretch()


# The plots that can be added to the dashboard, by the name shown for each.
PLOT_TYPES: dict[str, type[PlotPanel]] = {
    "Scatter": ScatterPanel,
    "Histogram": HistogramPanel,
}
