from contextlib import contextmanager

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import (
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QFrame,
    QGraphicsView,
    QHBoxLayout,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.tabs.placeholder import PlaceholderTab
from simmate.desktop.widgets import (
    NUMERIC_COLUMNS,
    ColumnChooser,
    CompoundDetails,
    CompoundFilterProxy,
    CompoundTable,
    CompoundTableModel,
    FilterPanel,
    HistogramPlot,
    PlotToolbar,
    PointTooltip,
    SettingsButton,
    SidePanel,
    StyledCheckBox,
    StyledComboBox,
    columns_icon,
    input_style,
)


class DashboardTab(QWidget):
    """A scatter plot and a histogram above a table, flanked by tabbed side panels, all kept in sync.

    - The left panel holds bulk tools; its Filters tab narrows everything: draw a substructure in the sketcher
      and/or set column filters. Filtered-out points/bars show in grey, or are hidden (plot settings).
    - Zooming/panning either plot further narrows the table to the compounds in view.
    - Hovering a point (or a row) highlights its row, rings its point, and outlines its histogram bin.
    - Hovering a point also shows a small card (structure + ID) beside the cursor
      (can be turned off in the plot settings).
    - Hovering a histogram bin highlights all of its rows and rings their points
      (can be turned off in the histogram settings).
    - Clicking points or bins (Ctrl+click to add/remove) selects rows; selecting rows rings
      their points and counts them in red in the histogram. Clicking empty plot space clears the selection.
    - The selected compound shows in full in the detail card (the right panel's Selection tab).
      It shows one compound at a time, so it shows a message instead while several are selected.
    - The table settings choose whether the table scrolls to hovered/selected points,
      and the columns button beside them chooses which columns show.

    Subclasses can add or swap side panel pages by overriding `get_left_pages` and
    `get_right_pages`.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.mdf = build_dataset()
        self.df = self.mdf.df
        self.model = CompoundTableModel(self.mdf)
        self.proxy = CompoundFilterProxy(self.model)

        # Our own record of the selection. The table's selection model forgets rows that
        # get filtered out, but we want them re-selected when they come back.
        self.selected_rows: set[int] = set()
        # the selected compound the detail card shows
        self.focus_row: int | None = None
        self._syncing = False

        # --- plot ---------------------------------------------------------------------
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
        self.show_filtered_checkbox.toggled.connect(self._redraw_points)

        self.hover_card_checkbox = StyledCheckBox("Show structure on hover")
        self.hover_card_checkbox.setToolTip(
            "Show a small card with the compound's structure beside the cursor\n"
            "while hovering a point"
        )
        self.hover_card_checkbox.setChecked(True)
        self.hover_card_checkbox.toggled.connect(
            lambda on: on or self.point_tooltip.hide()
        )

        self.plot = pg.PlotWidget(
            background=None
        )  # transparent: the window shows through
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        # Repaint the whole plot on any change. By default only the changed items'
        # bounds are repainted, but pyqtgraph's ScatterPlotItem.setData shrinks
        # those bounds before reporting the change, so points removed outside the
        # new bounds (e.g. hiding the grey points while zoomed in) linger on screen.
        self.plot.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )
        self.view_box = self.plot.getPlotItem().getViewBox()

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
        self.plot.getPlotItem().layout.addItem(color_bar, 2, 5)

        self.scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(None),
            hoverable=True,
            hoverSize=16,
            hoverPen=pg.mkPen("k", width=2),
            tip=None,  # the detail card replaces a text tooltip
        )
        self.scatter.sigHovered.connect(self._on_plot_hover)
        self.scatter.sigClicked.connect(self._on_plot_click)
        # after the points get the click, so we can tell when none was hit
        self.plot.scene().sigMouseClicked.connect(self._on_plot_background_click)
        self.point_tooltip = PointTooltip(self.plot)

        # Overlays drawn under the data points so they never steal hovers or clicks.
        self.dimmed_scatter = self._overlay(
            size=8, pen=pg.mkPen(None), brush=pg.mkBrush(150, 150, 150, 60)
        )
        self.selection_marks = self._overlay(
            size=19, pen=pg.mkPen("#ff5252", width=2.5)
        )
        # rings the hovered row's point, or a hovered bin's points
        self.hover_marks = self._overlay(size=24, pen=pg.mkPen("k", width=2))
        self.plot.addItem(self.scatter)

        # --- histogram ----------------------------------------------------------------
        self.hist_combo = StyledComboBox()
        self.hist_combo.addItems(NUMERIC_COLUMNS)
        self.hist_combo.setCurrentText("MolWt")
        self.hist_combo.currentTextChanged.connect(self._update_histogram)
        self.bins_combo = StyledComboBox()
        self.bins_combo.addItems(["10", "20", "30", "50"])
        self.bins_combo.setCurrentText("20")
        self.bins_combo.currentTextChanged.connect(self._update_histogram)

        self.hist_filtered_checkbox = StyledCheckBox(
            "Show filtered-out compounds in grey"
        )
        self.hist_filtered_checkbox.setToolTip(
            "Count compounds excluded by the filters in grey bars behind the others,\n"
            "instead of leaving them out"
        )
        self.hist_filtered_checkbox.setChecked(True)
        self.hist_filtered_checkbox.toggled.connect(self._redraw_histogram)

        self.bin_hover_checkbox = StyledCheckBox("Highlight a bin's compounds on hover")
        self.bin_hover_checkbox.setToolTip(
            "While hovering a bar, highlight its compounds' rows and ring\n"
            "their points in the scatter plot"
        )
        self.bin_hover_checkbox.setChecked(True)

        self.histogram = HistogramPlot()
        self.histogram.bin_hovered.connect(self._on_bin_hover)
        self.histogram.bin_clicked.connect(self._on_bin_click)
        self.histogram.background_clicked.connect(self._clear_selection)

        # Every pan/zoom step fires this; debounce so we filter once the view settles.
        self.range_timer = QTimer(self, singleShot=True, interval=80)
        self.range_timer.timeout.connect(self._filter_to_view)
        self.view_box.sigRangeChanged.connect(self.range_timer.start)
        self.histogram.view_box.sigRangeChanged.connect(self.range_timer.start)

        # --- detail card --------------------------------------------------------------
        self.details = CompoundDetails(self.mdf)
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidget(self.details)
        self.details_scroll.setWidgetResizable(True)
        # no frame, and the same padding as the filter panel (mirrored)
        self.details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.details_scroll.setContentsMargins(12, 8, 8, 8)

        # --- table --------------------------------------------------------------------
        self.table = CompoundTable(self.proxy)
        self.table.entered.connect(self._on_table_hover)
        # to notice the mouse leaving the table
        self.table.viewport().installEventFilter(self)
        self.table.selectionModel().selectionChanged.connect(self._on_table_selection)

        # --- side panels --------------------------------------------------------------
        # One page per tab; only the open tab's page shows.
        self.filter_panel = FilterPanel(self.mdf)
        self.filter_panel.filters_changed.connect(self._apply_filters)
        # re-draw thumbnails and the card with the new substructure highlighted & aligned
        self.filter_panel.query_changed.connect(self.model.set_highlight)
        self.filter_panel.query_changed.connect(self.details.set_query)
        left_pages = self.get_left_pages()
        # Filters starts open (when a subclass's pages still include it)
        left_widgets = [page for _, page in left_pages]
        self.left_panel = SidePanel(
            left_pages,
            side="left",
            width=385,
            min_width=385,
            current=(
                left_widgets.index(self.filter_panel)
                if self.filter_panel in left_widgets
                else 0
            ),
        )
        self.right_panel = SidePanel(
            self.get_right_pages(),
            side="right",
            width=385,
            min_width=385,
            open=False,  # starts collapsed
        )
        for panel in (self.left_panel, self.right_panel):
            panel.tabs.current_changed.connect(
                lambda index, panel=panel: self._show_side_page(panel, index)
            )

        # --- layout -------------------------------------------------------------------
        # The plot settings drop down from the gear button.
        plot_settings = QWidget()
        plot_settings.setStyleSheet(input_style())  # same inputs as the filters
        settings_layout = QFormLayout(plot_settings)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(10)
        settings_layout.addRow("X axis", self.x_combo)
        settings_layout.addRow("Y axis", self.y_combo)
        settings_layout.addRow(self.show_filtered_checkbox)
        settings_layout.addRow(self.hover_card_checkbox)

        controls = QHBoxLayout()
        controls.addWidget(PlotToolbar(self.plot))
        controls.addStretch()
        controls.addWidget(SettingsButton(plot_settings, tooltip="Plot settings"))

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(14)  # between the toolbar and the plot
        plot_layout.addLayout(controls)
        plot_layout.addWidget(self.plot, stretch=1)

        # The histogram gets the same toolbar and its own settings.
        hist_settings = QWidget()
        hist_settings.setStyleSheet(input_style())
        hist_settings_layout = QFormLayout(hist_settings)
        hist_settings_layout.setContentsMargins(12, 12, 12, 12)
        hist_settings_layout.setHorizontalSpacing(12)
        hist_settings_layout.setVerticalSpacing(10)
        hist_settings_layout.addRow("Column", self.hist_combo)
        hist_settings_layout.addRow("Bins", self.bins_combo)
        hist_settings_layout.addRow(self.hist_filtered_checkbox)
        hist_settings_layout.addRow(self.bin_hover_checkbox)

        hist_controls = QHBoxLayout()
        hist_controls.addWidget(PlotToolbar(self.histogram))
        hist_controls.addStretch()
        hist_controls.addWidget(
            SettingsButton(hist_settings, tooltip="Histogram settings")
        )

        hist_panel = QWidget()
        hist_layout = QVBoxLayout(hist_panel)
        hist_layout.setContentsMargins(0, 0, 0, 0)
        hist_layout.setSpacing(14)
        hist_layout.addLayout(hist_controls)
        hist_layout.addWidget(self.histogram, stretch=1)

        plots = QSplitter(Qt.Orientation.Horizontal)
        plots.setHandleWidth(14)  # doubles as the gap between the two plots
        plots.addWidget(plot_panel)
        plots.addWidget(hist_panel)
        plots.setSizes([500, 500])  # half each

        # Same row of controls over the table, with its own settings.
        self.scroll_to_hover_checkbox = StyledCheckBox("Scroll to hovered plot point")
        self.scroll_to_hover_checkbox.setToolTip(
            "Scroll the table to a compound's row while its point is hovered"
        )
        self.scroll_to_selection_checkbox = StyledCheckBox(
            "Scroll to selected plot point"
        )
        self.scroll_to_selection_checkbox.setToolTip(
            "Scroll the table to a compound's row when its point is clicked"
        )
        self.scroll_to_selection_checkbox.setChecked(True)
        table_settings = QWidget()
        table_settings.setStyleSheet(input_style())
        table_settings_layout = QFormLayout(table_settings)
        table_settings_layout.setContentsMargins(12, 12, 12, 12)
        table_settings_layout.setVerticalSpacing(10)
        table_settings_layout.addRow(self.scroll_to_hover_checkbox)
        table_settings_layout.addRow(self.scroll_to_selection_checkbox)
        column_chooser = ColumnChooser(self.table)
        column_chooser.setStyleSheet(input_style())
        table_controls = QHBoxLayout()
        table_controls.setSpacing(2)  # the two buttons sit close together
        table_controls.addStretch()
        table_controls.addWidget(
            SettingsButton(
                column_chooser, tooltip="Show/hide columns", icon=columns_icon()
            )
        )
        table_controls.addWidget(
            SettingsButton(table_settings, tooltip="Table settings")
        )

        table_panel = QWidget()
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(6)  # between the gear and the table
        table_layout.addLayout(table_controls)
        table_layout.addWidget(self.table, stretch=1)

        main = QSplitter(Qt.Orientation.Vertical)
        # The handle doubles as the gap between the plot and the table (the table's
        # gear row adds a bit more).
        main.setHandleWidth(6)
        main.addWidget(plots)
        main.addWidget(table_panel)
        main.setSizes([440, 420])

        # Each tab bar sits just inside its splitter handle, so it hugs its panel's
        # edge when open and the window's edge when collapsed.
        main_with_tabs = QWidget()
        tabs_layout = QHBoxLayout(main_with_tabs)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(14)
        tabs_layout.addWidget(self.left_panel.tabs)
        tabs_layout.addWidget(main, stretch=1)
        tabs_layout.addWidget(self.right_panel.tabs)

        # Only the side panels can collapse: by closing their open tab or by
        # dragging their handle all the way to the window's edge.
        self.outer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.outer_splitter.setHandleWidth(3)
        self.outer_splitter.addWidget(self.left_panel)
        self.outer_splitter.addWidget(main_with_tabs)
        self.outer_splitter.addWidget(self.right_panel)
        self.outer_splitter.setCollapsible(1, False)
        # Extra width (e.g. a bigger window) goes to the center, so the side panels
        # open at their set widths.
        for index, stretch in enumerate([0, 1, 0]):
            self.outer_splitter.setStretchFactor(index, stretch)
        left, right = (
            panel.open_width if panel.tabs.current() >= 0 else 0  # 0 = collapsed
            for panel in (self.left_panel, self.right_panel)
        )
        self.outer_splitter.setSizes([left, 640, right])
        self.outer_splitter.splitterMoved.connect(self._sync_side_tabs)

        layout = QVBoxLayout(self)
        layout.addWidget(self.outer_splitter)

        self._update_histogram()  # before the filters, which redraw its bars
        self._apply_filters()
        self._update_axes()
        # Again once the window is listening, so the count replaces its "Ready".
        QTimer.singleShot(0, self._update_count)

    # --- side panel pages -----------------------------------------------------------------

    def get_left_pages(self) -> list[tuple[str, QWidget]]:
        """The (title, page) pairs of the left panel, for bulk / table operations.

        Tabs not built yet open a "coming soon" page for now.
        """
        return [
            ("Logs", PlaceholderTab("Logs")),
            ("Filter", self.filter_panel),
            ("Featurize", PlaceholderTab("Featurize")),
            ("Analyze", PlaceholderTab("Analyze")),
        ]

    def get_right_pages(self) -> list[tuple[str, QWidget]]:
        """The (title, page) pairs of the right panel, for work on the selected compound(s).

        Tabs not built yet open a "coming soon" page for now.
        """
        return [
            ("Select", self.details_scroll),
            ("Transform", PlaceholderTab("Transform")),
            ("Calcs", PlaceholderTab("Calcs")),
            ("Enumerate", PlaceholderTab("Enumerate")),
        ]

    # --- helpers --------------------------------------------------------------------------

    def _overlay(self, size, pen, brush=None) -> pg.ScatterPlotItem:
        item = pg.ScatterPlotItem(size=size, pen=pen, brush=brush or pg.mkBrush(None))
        item.setZValue(-1)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(item)
        return item

    def _xy(self, row_indices) -> tuple[np.ndarray, np.ndarray]:
        x_key, y_key = self.x_combo.currentText(), self.y_combo.currentText()
        row_indices = list(row_indices)
        return (
            self.df[x_key].to_numpy()[row_indices],
            self.df[y_key].to_numpy()[row_indices],
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

    def _proxy_index(self, row: int):
        return self.proxy.mapFromSource(self.model.index(row, 0))

    def _show_hovered(self, rows: set[int]):
        """Highlight `rows` in the table (none when empty)."""
        self.model.set_highlighted_rows(rows)

    def _show_selection_card(self):
        if len(self.selected_rows) > 1:
            self.details.show_many(len(self.selected_rows))
        else:
            self.details.show_row(self.focus_row)

    def _mark_hovered(self, rows, size: int = 24):
        """Ring the points of `rows` in the scatter plot (none when empty)."""
        x, y = self._xy(sorted(rows))
        self.hover_marks.setData(x=x, y=y, size=size)

    def _focus_bin_of(self, row: int | None):
        """Outline the histogram bin holding `row`, or no bin when None."""
        self.histogram.set_focus_bin(
            None if row is None else int(self.histogram.bin_of_row[row])
        )

    def _update_count(self):
        shown = self.proxy.rowCount()
        self.status.emit(f"{shown} of {self.df.height} compounds shown")

    # --- side panels -----------------------------------------------------------------------

    def _show_side_page(self, panel: SidePanel, index: int):
        """Open `panel` on page `index`, or collapse it when -1."""
        self._update_min_widths(panel)
        sizes = self.outer_splitter.sizes()
        i = self.outer_splitter.indexOf(panel)
        if index < 0:
            if sizes[i] > 0:
                panel.open_width = sizes[i]
            sizes[1] += sizes[i]
            sizes[i] = 0
        else:
            panel.setCurrentIndex(index)
            if sizes[i] == 0:
                # take the space from the center, but never more than half of it
                sizes[i] = min(panel.open_width, sizes[1] // 2)
                sizes[1] -= sizes[i]
        self.outer_splitter.setSizes(sizes)

    def _update_min_widths(self, panel: SidePanel):
        # A panel's minimum width depends on whether it's open; have the splitter and
        # the layouts above it re-read it.
        panel.updateGeometry()
        self.outer_splitter.updateGeometry()

    def _sync_side_tabs(self, *_):
        # The user dragged a handle: dragged shut closes the panel's open tab, and
        # dragged back open re-opens the page that was showing.
        for panel in (self.left_panel, self.right_panel):
            width = self.outer_splitter.sizes()[self.outer_splitter.indexOf(panel)]
            if width == 0:
                panel.tabs.set_current(-1, emit=False)
            else:
                panel.open_width = width
                if panel.tabs.current() < 0:
                    panel.tabs.set_current(panel.currentIndex(), emit=False)
            self._update_min_widths(panel)

    # --- filters ----------------------------------------------------------------------------

    @contextmanager
    def _refiltering(self):
        """Wrap a change to the table's rows: the selection churn it causes is ignored,
        then rows of our selection that are (back) in the table are re-selected."""
        self._syncing = True
        try:
            yield
            self._select_in_table(self.selected_rows, scroll=False)
        finally:
            self._syncing = False

    def _apply_filters(self):
        with self._refiltering():
            self.proxy.set_filters(**self.filter_panel.filters())
        self._redraw_points()
        self._update_count()

    def _redraw_points(self):
        passing = self.proxy.passing
        shown = np.flatnonzero(passing).tolist()
        x, y = self._xy(shown)
        self.scatter.setData(
            x=x, y=y, brush=[self.brushes[i] for i in shown], data=shown
        )
        if self.show_filtered_checkbox.isChecked():
            x, y = self._xy(np.flatnonzero(~passing))
            self.dimmed_scatter.setData(x=x, y=y)
        else:
            # Not .clear(): it skips prepareGeometryChange, so Qt never repaints the
            # area the old points covered and they linger on screen.
            self.dimmed_scatter.setData(x=[], y=[])
        self._refresh_selection_marks()
        self._mark_hovered([])
        self.point_tooltip.hide()
        self._redraw_histogram()

    # --- histogram ---------------------------------------------------------------------------

    def _update_histogram(self):
        """Re-bin the histogram after its column or bin count changed."""
        key = self.hist_combo.currentText()
        self.histogram.set_values(
            self.df[key].to_numpy(), int(self.bins_combo.currentText())
        )
        self._redraw_histogram()
        self.histogram.setLabel("bottom", key)
        self.histogram.view_box.autoRange()  # triggers _filter_to_view via sigRangeChanged

    def _redraw_histogram(self):
        self.histogram.set_passing(
            self.proxy.passing, self.hist_filtered_checkbox.isChecked()
        )

    def _on_bin_hover(self, bin: int | None):
        self.histogram.set_focus_bin(bin)
        if bin is None:
            self._mark_hovered([])
            self._show_hovered(set())
            self._update_count()  # back to the count once off the bars
            return
        rows = set(self.histogram.rows_in_bin(bin))
        low, high = self.histogram.bin_range(bin)
        self.status.emit(
            f"{self.hist_combo.currentText()} {low:.4g} to {high:.4g}: "
            f"{len(rows)} compound(s)"
        )
        if self.bin_hover_checkbox.isChecked():
            self._mark_hovered(rows, size=16)
            self._show_hovered(rows)

    def _on_bin_click(self, bin: int, modifiers):
        rows = set(self.histogram.rows_in_bin(bin))
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # add the bin, or remove it when it's all selected already
            if rows <= self.selected_rows:
                rows = self.selected_rows - rows
            else:
                rows = self.selected_rows | rows
        self._select_in_table(
            rows, scroll=self.scroll_to_selection_checkbox.isChecked()
        )

    def _clear_selection(self):
        self.table.clearSelection()

    # --- plot -> table ----------------------------------------------------------------------

    def _update_axes(self):
        self._redraw_points()
        self.plot.setLabel("bottom", self.x_combo.currentText())
        self.plot.setLabel("left", self.y_combo.currentText())
        self.view_box.autoRange()  # triggers _filter_to_view via sigRangeChanged

    def _filter_to_view(self):
        self.point_tooltip.hide()  # its point has moved out from under it
        (x_min, x_max), (y_min, y_max) = self.view_box.viewRange()
        (hist_min, hist_max), _ = self.histogram.view_box.viewRange()
        with self._refiltering():
            self.proxy.set_view_ranges(
                [
                    (self.x_combo.currentText(), x_min, x_max),
                    (self.y_combo.currentText(), y_min, y_max),
                    (self.hist_combo.currentText(), hist_min, hist_max),
                ]
            )
        self._update_count()

    def _on_plot_hover(self, _item, points, event):
        # Empty when the cursor leaves the points; the card falls back to the selection.
        row = self._nearest(points, event)
        self._show_hovered(set() if row is None else {row})
        self._focus_bin_of(row)
        if row is not None:
            if self.scroll_to_hover_checkbox.isChecked():
                self.table.scrollTo(
                    self._proxy_index(row), QAbstractItemView.ScrollHint.EnsureVisible
                )
            if self.hover_card_checkbox.isChecked():
                self.point_tooltip.show_at(
                    self.details.svg(row),
                    self.df["id"][row],
                    self.plot.mapFromScene(event.scenePos()),
                )
            self.status.emit(f"{self.df['id'][row]}: pIC50 {self.df['pIC50'][row]}")
        else:
            self.point_tooltip.hide()
            self._update_count()  # back to the count once off the points

    def _on_plot_click(self, _item, points, event):
        clicked = self._nearest(points, event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            rows = self.selected_rows ^ {clicked}  # toggle
        else:
            rows = {clicked}
        self._select_in_table(
            rows, scroll=self.scroll_to_selection_checkbox.isChecked(), current=clicked
        )
        event.accept()

    def _on_plot_background_click(self, event):
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
        self._clear_selection()

    def _select_in_table(
        self, rows: set[int], scroll: bool, current: int | None = None
    ):
        selection = QItemSelection()
        for row in rows:
            index = self._proxy_index(row)
            if index.isValid():  # invalid = currently filtered out of the table
                selection.select(index, index)
        flags = (
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows
        )
        selection_model = self.table.selectionModel()
        if current in rows:
            # also make the clicked row "current" so the card focuses on it
            selection_model.setCurrentIndex(
                self._proxy_index(current), QItemSelectionModel.SelectionFlag.NoUpdate
            )
        selection_model.select(selection, flags)
        if scroll and not selection.isEmpty():
            self.table.scrollTo(
                selection.indexes()[0], QAbstractItemView.ScrollHint.EnsureVisible
            )

    # --- table -> plot ----------------------------------------------------------------------

    def _on_table_selection(self, *_):
        if self._syncing:
            return  # selection churn caused by filtering, not by the user
        indexes = self.table.selectionModel().selectedRows()
        self.selected_rows = {self.proxy.mapToSource(i).row() for i in indexes}

        current = self.table.selectionModel().currentIndex()
        current_row = (
            self.proxy.mapToSource(current).row() if current.isValid() else None
        )
        if current_row in self.selected_rows:
            self.focus_row = current_row
        elif self.selected_rows:
            self.focus_row = min(self.selected_rows)
        else:
            self.focus_row = None
        self._show_selection_card()

        self._refresh_selection_marks()
        if self.selected_rows:
            self.status.emit(f"{len(self.selected_rows)} compound(s) selected")

    def _refresh_selection_marks(self):
        passing = self.proxy.passing
        x, y = self._xy(sorted(r for r in self.selected_rows if passing[r]))
        self.selection_marks.setData(x=x, y=y)
        self.histogram.set_selected(self.selected_rows)

    def _on_table_hover(self, index):
        row = self.proxy.mapToSource(index).row()
        self._mark_hovered([row])
        self._show_hovered({row})
        self._focus_bin_of(row)

    def eventFilter(self, watched, event):
        if watched is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self._mark_hovered([])
            self._show_hovered(set())
            self._focus_bin_of(None)
        return super().eventFilter(watched, event)
