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
    QCheckBox,
    QFormLayout,
    QFrame,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.tabs.placeholder import PlaceholderTab
from simmate.desktop.theme import MUTED_COLOR
from simmate.desktop.widgets import (
    NUMERIC_COLUMNS,
    CompoundDetails,
    CompoundFilterProxy,
    CompoundTable,
    CompoundTableModel,
    FilterPanel,
    PlotToolbar,
    SettingsButton,
    SidePanel,
    StyledComboBox,
    input_style,
)

# Side panel tabs not built yet; each opens a "coming soon" page for now.
# Left: bulk / many-compound / table operations. Right: single-compound work.
LEFT_PLACEHOLDERS = ["Featurizers", "Clustering", "ChemSpace", "ML/AI", "Diversity"]
RIGHT_PLACEHOLDERS = ["Mutations", "Conformers", "Calculations"]


class DashboardTab(QWidget):
    """A scatter plot and a table, flanked by tabbed side panels, all kept in sync.

    - The left panel holds bulk tools; its Filters tab narrows everything: draw a substructure in the sketcher
      and/or set column filters. Filtered-out points show in grey, or are hidden (plot settings).
    - Zooming/panning the plot further narrows the table to the points in view.
    - Hovering a point (or a row) highlights its row, rings its point, and shows it in full
      in the detail card (the right panel's Compound tab). When the hover ends, the card goes back to the selected compound.
    - Clicking points (Ctrl+click to add/remove) selects rows; selecting rows rings their points.
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
        # what the detail card shows when nothing is hovered
        self.focus_row: int | None = None
        self._syncing = False

        # --- plot ---------------------------------------------------------------------
        self.x_combo = StyledComboBox()
        self.y_combo = StyledComboBox()
        for combo, default in [(self.x_combo, "cLogP"), (self.y_combo, "pIC50")]:
            combo.addItems(NUMERIC_COLUMNS)
            combo.setCurrentText(default)
            combo.currentTextChanged.connect(self._update_axes)

        self.show_filtered_checkbox = QCheckBox("Show filtered-out points in grey")
        self.show_filtered_checkbox.setToolTip(
            "Keep compounds excluded by the filters on the plot as grey points,\n"
            "instead of hiding them"
        )
        self.show_filtered_checkbox.setChecked(True)
        self.show_filtered_checkbox.toggled.connect(self._redraw_points)

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

        # Overlays drawn under the data points so they never steal hovers or clicks.
        self.dimmed_scatter = self._overlay(
            size=8, pen=pg.mkPen(None), brush=pg.mkBrush(150, 150, 150, 60)
        )
        self.selection_marks = self._overlay(
            size=19, pen=pg.mkPen("#ff5252", width=2.5)
        )
        self.table_hover_mark = self._overlay(size=24, pen=pg.mkPen("k", width=2))
        self.plot.addItem(self.scatter)

        # Every pan/zoom step fires this; debounce so we filter once the view settles.
        self.range_timer = QTimer(self, singleShot=True, interval=80)
        self.range_timer.timeout.connect(self._filter_to_view)
        self.view_box.sigRangeChanged.connect(self.range_timer.start)

        # --- detail card --------------------------------------------------------------
        self.details = CompoundDetails(self.mdf)
        details_scroll = QScrollArea()
        details_scroll.setWidget(self.details)
        details_scroll.setWidgetResizable(True)
        # no frame, and the same padding as the filter panel (mirrored)
        details_scroll.setFrameShape(QFrame.Shape.NoFrame)
        details_scroll.setContentsMargins(12, 8, 8, 8)

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
        self.left_panel = SidePanel(
            [("Filters", self.filter_panel)]
            + [(title, PlaceholderTab(title)) for title in LEFT_PLACEHOLDERS],
            side="left",
            width=420,
            min_width=300,
        )
        self.right_panel = SidePanel(
            [("Compound", details_scroll)]
            + [(title, PlaceholderTab(title)) for title in RIGHT_PLACEHOLDERS],
            side="right",
            width=340,
            min_width=280,
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

        # Same row of controls over the table, with its settings still to come.
        table_settings = QLabel("Table settings are coming soon.")
        table_settings.setStyleSheet(f"color: {MUTED_COLOR}; padding: 12px;")
        table_controls = QHBoxLayout()
        table_controls.addStretch()
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
        main.addWidget(plot_panel)
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
        self.outer_splitter.setSizes(
            [self.left_panel.open_width, 640, self.right_panel.open_width]
        )
        self.outer_splitter.splitterMoved.connect(self._sync_side_tabs)

        layout = QVBoxLayout(self)
        layout.addWidget(self.outer_splitter)

        self._apply_filters()
        self._update_axes()
        # Again once the window is listening, so the count replaces its "Ready".
        QTimer.singleShot(0, self._update_count)

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

    def _show_hovered(self, row: int | None):
        """Highlight `row` everywhere, or fall back to the focused selection when None."""
        self.model.set_highlighted_rows(set() if row is None else {row})
        self.details.show_row(self.focus_row if row is None else row)

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
        self.table_hover_mark.setData(x=[], y=[])

    # --- plot -> table ----------------------------------------------------------------------

    def _update_axes(self):
        self._redraw_points()
        self.plot.setLabel("bottom", self.x_combo.currentText())
        self.plot.setLabel("left", self.y_combo.currentText())
        self.view_box.autoRange()  # triggers _filter_to_view via sigRangeChanged

    def _filter_to_view(self):
        (x_min, x_max), (y_min, y_max) = self.view_box.viewRange()
        with self._refiltering():
            self.proxy.set_view_ranges(
                [
                    (self.x_combo.currentText(), x_min, x_max),
                    (self.y_combo.currentText(), y_min, y_max),
                ]
            )
        self._update_count()

    def _on_plot_hover(self, _item, points, event):
        # Empty when the cursor leaves the points; the card falls back to the selection.
        row = self._nearest(points, event)
        self._show_hovered(row)
        if row is not None:
            self.table.scrollTo(
                self._proxy_index(row), QAbstractItemView.ScrollHint.EnsureVisible
            )
            self.status.emit(f"{self.df['id'][row]}: pIC50 {self.df['pIC50'][row]}")
        else:
            self._update_count()  # back to the count once off the points

    def _on_plot_click(self, _item, points, event):
        clicked = self._nearest(points, event)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            rows = self.selected_rows ^ {clicked}  # toggle
        else:
            rows = {clicked}
        self._select_in_table(rows, scroll=True, current=clicked)
        event.accept()

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
        self.details.show_row(self.focus_row)

        self._refresh_selection_marks()
        if self.selected_rows:
            self.status.emit(f"{len(self.selected_rows)} compound(s) selected")

    def _refresh_selection_marks(self):
        passing = self.proxy.passing
        x, y = self._xy(sorted(r for r in self.selected_rows if passing[r]))
        self.selection_marks.setData(x=x, y=y)

    def _on_table_hover(self, index):
        row = self.proxy.mapToSource(index).row()
        x, y = self._xy([row])
        self.table_hover_mark.setData(x=x, y=y)
        self._show_hovered(row)

    def eventFilter(self, watched, event):
        if watched is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self.table_hover_mark.setData(x=[], y=[])
            self._show_hovered(None)
        return super().eventFilter(watched, event)
