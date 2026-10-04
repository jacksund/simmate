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
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.compounds import build_dataset
from simmate.desktop.tabs.table import (
    NUMERIC_COLUMNS,
    THUMBNAIL_SIZE,
    CompoundFilterProxy,
    CompoundTableModel,
)
from simmate.desktop.utilities import PlotToolbar


class LinkedTab(QWidget):
    """A scatter plot and a table showing the same compounds, kept in sync.

    - Zooming/panning the plot filters the table to the points in view.
    - Hovering a point highlights its row; hovering a row marks its point.
    - Clicking points (Ctrl+click to add/remove) selects rows; selecting rows rings their points.
    """

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.rows = build_dataset()
        self.model = CompoundTableModel(self.rows)
        self.proxy = CompoundFilterProxy()
        self.proxy.setSourceModel(self.model)

        # Our own record of the selection. The table's selection model forgets rows that
        # get filtered out, but we want them re-selected when you zoom back out.
        self.selected_rows: set[int] = set()
        self._syncing = False

        # --- plot ---------------------------------------------------------------------
        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
        for combo, default in [(self.x_combo, "cLogP"), (self.y_combo, "pIC50")]:
            combo.addItems(NUMERIC_COLUMNS)
            combo.setCurrentText(default)
            combo.currentTextChanged.connect(self._update_axes)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.view_box = self.plot.getPlotItem().getViewBox()

        pic50 = np.array([r["pIC50"] for r in self.rows])
        colors = pg.colormap.get("viridis").map(
            (pic50 - pic50.min()) / np.ptp(pic50), mode="qcolor"
        )
        self.brushes = [pg.mkBrush(c) for c in colors]

        self.scatter = pg.ScatterPlotItem(
            size=10,
            pen=pg.mkPen(None),
            hoverable=True,
            hoverSize=16,
            hoverPen=pg.mkPen("w", width=2),
            tip=None,
        )
        self.scatter.sigHovered.connect(self._on_plot_hover)
        self.scatter.sigClicked.connect(self._on_plot_click)

        # Overlays drawn under the data points so they never steal hovers or clicks.
        self.selection_marks = self._overlay(
            size=19, pen=pg.mkPen("#ff5252", width=2.5)
        )
        self.table_hover_mark = self._overlay(size=24, pen=pg.mkPen("w", width=2))
        self.plot.addItem(self.scatter)

        # Every pan/zoom step fires this; debounce so we filter once the view settles.
        self.range_timer = QTimer(self, singleShot=True, interval=80)
        self.range_timer.timeout.connect(self._filter_to_view)
        self.view_box.sigRangeChanged.connect(self.range_timer.start)

        # --- table --------------------------------------------------------------------
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(self._column("pIC50"), Qt.SortOrder.DescendingOrder)
        self.table.setIconSize(THUMBNAIL_SIZE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(THUMBNAIL_SIZE.height() + 6)
        self.table.horizontalHeader().setStretchLastSection(True)
        for key in ("smiles", "tested"):
            self.table.setColumnHidden(self._column(key), True)
        for column in range(1, self.model.columnCount()):
            self.table.resizeColumnToContents(column)
        self.table.setColumnWidth(0, THUMBNAIL_SIZE.width() + 10)

        self.table.setMouseTracking(True)  # needed for the `entered` (hover) signal
        self.table.entered.connect(self._on_table_hover)
        self.table.viewport().installEventFilter(
            self
        )  # to notice the mouse leaving the table
        self.table.selectionModel().selectionChanged.connect(self._on_table_selection)

        # --- layout -------------------------------------------------------------------
        self.count_label = QLabel()
        controls = QHBoxLayout()
        controls.addWidget(QLabel("X:"))
        controls.addWidget(self.x_combo)
        controls.addWidget(QLabel("Y:"))
        controls.addWidget(self.y_combo)
        controls.addWidget(PlotToolbar(self.plot))
        controls.addStretch()
        controls.addWidget(self.count_label)

        splitter = QSplitter()
        splitter.addWidget(self.plot)
        splitter.addWidget(self.table)
        splitter.setSizes([520, 680])

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(splitter, stretch=1)

        self._update_axes()

    # --- helpers --------------------------------------------------------------------------

    def _overlay(self, size, pen) -> pg.ScatterPlotItem:
        item = pg.ScatterPlotItem(size=size, pen=pen, brush=pg.mkBrush(None))
        item.setZValue(-1)
        item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.plot.addItem(item)
        return item

    def _column(self, key: str) -> int:
        return [k for _, k in self.model.COLUMNS].index(key)

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

    # --- plot -> table ----------------------------------------------------------------------

    def _update_axes(self):
        x, y = self._xy(range(len(self.rows)))
        self.scatter.setData(
            x=x, y=y, brush=self.brushes, data=list(range(len(self.rows)))
        )
        self.plot.setLabel("bottom", self.x_combo.currentText())
        self.plot.setLabel("left", self.y_combo.currentText())
        self._refresh_selection_marks()
        self.table_hover_mark.clear()
        self.view_box.autoRange()  # triggers _filter_to_view via sigRangeChanged

    def _filter_to_view(self):
        (x_min, x_max), (y_min, y_max) = self.view_box.viewRange()
        self._syncing = True
        self.proxy.set_filters(
            value_ranges=[
                (self.x_combo.currentText(), x_min, x_max),
                (self.y_combo.currentText(), y_min, y_max),
            ]
        )
        self._select_in_table(
            self.selected_rows, scroll=False
        )  # restore rows that came back into view
        self._syncing = False

        shown = self.proxy.rowCount()
        self.count_label.setText(f"{shown} of {len(self.rows)} compounds in view")
        self.status.emit(f"Table filtered to the {shown} compounds visible in the plot")

    def _on_plot_hover(self, _item, points, event):
        row = self._nearest(points, event)
        self.model.set_highlighted_rows(set() if row is None else {row})
        if row is not None:
            self.table.scrollTo(
                self._proxy_index(row), QAbstractItemView.ScrollHint.EnsureVisible
            )
            self.status.emit(f"{self.rows[row]['id']}: pIC50 {self.rows[row]['pIC50']}")

    def _on_plot_click(self, _item, points, event):
        clicked = {self._nearest(points, event)}
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            rows = self.selected_rows ^ clicked  # toggle
        else:
            rows = clicked
        self._select_in_table(rows, scroll=True)
        event.accept()

    def _select_in_table(self, rows: set[int], scroll: bool):
        selection = QItemSelection()
        for row in rows:
            index = self._proxy_index(row)
            if index.isValid():  # invalid = currently filtered out of the table
                selection.select(index, index)
        flags = (
            QItemSelectionModel.SelectionFlag.ClearAndSelect
            | QItemSelectionModel.SelectionFlag.Rows
        )
        self.table.selectionModel().select(selection, flags)
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
        self._refresh_selection_marks()
        if self.selected_rows:
            self.status.emit(f"{len(self.selected_rows)} compound(s) selected")

    def _refresh_selection_marks(self):
        x, y = self._xy(sorted(self.selected_rows))
        self.selection_marks.setData(x=x, y=y)

    def _on_table_hover(self, index):
        x, y = self._xy([self.proxy.mapToSource(index).row()])
        self.table_hover_mark.setData(x=x, y=y)

    def eventFilter(self, watched, event):
        if watched is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self.table_hover_mark.clear()
        return super().eventFilter(watched, event)
