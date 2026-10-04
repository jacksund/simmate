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
    QComboBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.utilities import PlotToolbar
from simmate.desktop.widgets import (
    NUMERIC_COLUMNS,
    THUMBNAIL_SIZE,
    CompoundDetails,
    CompoundFilterProxy,
    CompoundTableModel,
    FilterPanel,
)


class DashboardTab(QWidget):
    """A scatter plot, a compound detail card, and a table, all kept in sync, plus filters.

    - The filter column (left) narrows everything: draw a substructure in the sketcher
      and/or set column filters. Filtered-out points are hidden, or dimmed if toggled.
    - Zooming/panning the plot further narrows the table to the points in view.
    - Hovering a point (or a row) highlights its row, rings its point, and shows it in full
      in the detail card. When the hover ends, the card goes back to the selected compound.
    - Clicking points (Ctrl+click to add/remove) selects rows; selecting rows rings their points.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.rows = build_dataset()
        self.model = CompoundTableModel(self.rows)
        self.proxy = CompoundFilterProxy()
        self.proxy.setSourceModel(self.model)

        # Which rows pass the filter column (ignoring the plot's view), by row index.
        self.passing = [True] * len(self.rows)
        # Our own record of the selection. The table's selection model forgets rows that
        # get filtered out, but we want them re-selected when they come back.
        self.selected_rows: set[int] = set()
        self.focus_row: int | None = (
            None  # what the detail card shows when nothing is hovered
        )
        self._syncing = False

        # --- plot ---------------------------------------------------------------------
        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
        for combo, default in [(self.x_combo, "cLogP"), (self.y_combo, "pIC50")]:
            combo.addItems(NUMERIC_COLUMNS)
            combo.setCurrentText(default)
            combo.currentTextChanged.connect(self._update_axes)

        self.dim_checkbox = QCheckBox("Dim filtered-out")
        self.dim_checkbox.setToolTip(
            "Show compounds excluded by the filters as grey points instead of hiding them"
        )
        self.dim_checkbox.toggled.connect(self._redraw_points)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.view_box = self.plot.getPlotItem().getViewBox()

        # Color every point by potency so trends are visible regardless of the chosen axes.
        pic50 = np.array([r["pIC50"] for r in self.rows])
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
        self.details = CompoundDetails(self.rows)
        details_scroll = QScrollArea()
        details_scroll.setWidget(self.details)
        details_scroll.setWidgetResizable(True)

        # --- table --------------------------------------------------------------------
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(
            self.model.column("pIC50"), Qt.SortOrder.DescendingOrder
        )
        self.table.setIconSize(THUMBNAIL_SIZE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(THUMBNAIL_SIZE.height() + 6)
        self.table.horizontalHeader().setStretchLastSection(True)
        for key in ("smiles", "tested"):
            self.table.setColumnHidden(self.model.column(key), True)
        # Size text columns to fit. Skip the image column: measuring it would render every image.
        for column in range(1, self.model.columnCount()):
            self.table.resizeColumnToContents(column)
        self.table.setColumnWidth(0, THUMBNAIL_SIZE.width() + 10)

        self.table.setMouseTracking(True)  # needed for the `entered` (hover) signal
        self.table.entered.connect(self._on_table_hover)
        # to notice the mouse leaving the table
        self.table.viewport().installEventFilter(self)
        self.table.selectionModel().selectionChanged.connect(self._on_table_selection)

        # --- filter column ------------------------------------------------------------
        self.filter_panel = FilterPanel(self.rows)
        self.filter_panel.filters_changed.connect(self._apply_filters)

        # --- layout -------------------------------------------------------------------
        self.count_label = QLabel()
        controls = QHBoxLayout()
        controls.addWidget(QLabel("X:"))
        controls.addWidget(self.x_combo)
        controls.addWidget(QLabel("Y:"))
        controls.addWidget(self.y_combo)
        controls.addWidget(PlotToolbar(self.plot))
        controls.addWidget(self.dim_checkbox)
        controls.addStretch()
        controls.addWidget(self.count_label)

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addLayout(controls)
        plot_layout.addWidget(self.plot, stretch=1)

        top = QSplitter(Qt.Orientation.Horizontal)
        top.addWidget(plot_panel)
        top.addWidget(details_scroll)
        top.setSizes([640, 340])

        main = QSplitter(Qt.Orientation.Vertical)
        main.addWidget(top)
        main.addWidget(self.table)
        main.setSizes([440, 420])

        outer = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(self.filter_panel)
        outer.addWidget(main)
        outer.setSizes([420, 980])

        layout = QVBoxLayout(self)
        layout.addWidget(outer)

        self._apply_filters()
        self._update_axes()

    # --- helpers --------------------------------------------------------------------------

    def _overlay(self, size, pen, brush=None) -> pg.ScatterPlotItem:
        item = pg.ScatterPlotItem(size=size, pen=pen, brush=brush or pg.mkBrush(None))
        item.setZValue(-1)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(item)
        return item

    def _xy(self, row_indices) -> tuple[list, list]:
        x_key, y_key = self.x_combo.currentText(), self.y_combo.currentText()
        return [self.rows[i][x_key] for i in row_indices], [
            self.rows[i][y_key] for i in row_indices
        ]

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
        self.count_label.setText(f"{shown} of {len(self.rows)} compounds shown")
        self.status.emit(f"{shown} compounds pass the filters and are in view")

    # --- filters ----------------------------------------------------------------------------

    def _apply_filters(self):
        filters = self.filter_panel.filters()
        query = filters["query"]
        if query is not self.model.highlight_query:
            # re-draw thumbnails and the card with the new substructure highlighted & aligned
            self.model.set_highlight(query)
            self.details.set_query(query)

        self._syncing = True
        self.proxy.set_filters(**filters)
        self._select_in_table(self.selected_rows, scroll=False)
        self._syncing = False

        self.passing = [self.proxy.accepts(r, include_view=False) for r in self.rows]
        self._redraw_points()
        self._update_count()

    def _redraw_points(self):
        shown = [i for i, ok in enumerate(self.passing) if ok]
        x, y = self._xy(shown)
        self.scatter.setData(
            x=x, y=y, brush=[self.brushes[i] for i in shown], data=shown
        )
        if self.dim_checkbox.isChecked():
            x, y = self._xy([i for i, ok in enumerate(self.passing) if not ok])
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
        self._syncing = True
        self.proxy.set_view_ranges(
            [
                (self.x_combo.currentText(), x_min, x_max),
                (self.y_combo.currentText(), y_min, y_max),
            ]
        )
        # restore rows that came back into view
        self._select_in_table(self.selected_rows, scroll=False)
        self._syncing = False
        self._update_count()

    def _on_plot_hover(self, _item, points, event):
        # Empty when the cursor leaves the points; the card falls back to the selection.
        row = self._nearest(points, event)
        self._show_hovered(row)
        if row is not None:
            self.table.scrollTo(
                self._proxy_index(row), QAbstractItemView.ScrollHint.EnsureVisible
            )
            self.status.emit(f"{self.rows[row]['id']}: pIC50 {self.rows[row]['pIC50']}")

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
        if current is not None and current in rows:
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
        x, y = self._xy(sorted(r for r in self.selected_rows if self.passing[r]))
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
