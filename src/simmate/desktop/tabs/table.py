from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from rdkit import Chem

from simmate.desktop.example_data.compounds import SCAFFOLDS, build_dataset
from simmate.desktop.utilities import mol_to_png

# Raw values for sorting (so 10 sorts after 9), separate from the displayed text.
SORT_ROLE = Qt.ItemDataRole.UserRole

NUMERIC_COLUMNS = ["pIC50", "solubility", "MolWt", "cLogP", "TPSA"]
THUMBNAIL_SIZE = QSize(180, 120)
HIGHLIGHT_COLOR = QColor("#6d5a00")


class CompoundTableModel(QAbstractTableModel):
    """Exposes the dataset to Qt views. The view only asks for cells it's about to paint."""

    COLUMNS = [
        ("Structure", "structure"),
        ("ID", "id"),
        ("Series", "series"),
        ("SMILES", "smiles"),
        ("pIC50", "pIC50"),
        ("Solubility (µM)", "solubility"),
        ("MolWt", "MolWt"),
        ("cLogP", "cLogP"),
        ("TPSA", "TPSA"),
        ("Status", "status"),
        ("Tested", "tested"),
    ]

    def __init__(self, rows: list[dict]):
        super().__init__()
        self.rows = rows
        self.highlight_query: Chem.Mol | None = None
        self.pixmap_cache: dict[int, QPixmap] = {}
        self.highlighted_rows: set[int] = set()  # e.g. rows whose plot point is hovered

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.COLUMNS[section][0]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row = self.rows[index.row()]
        key = self.COLUMNS[index.column()][1]

        if (
            role == Qt.ItemDataRole.BackgroundRole
            and index.row() in self.highlighted_rows
        ):
            return HIGHLIGHT_COLOR

        if key == "structure":
            if role == Qt.ItemDataRole.DecorationRole:
                return self._thumbnail(index.row())
            if role == SORT_ROLE:
                return row[
                    "mol"
                ].GetNumHeavyAtoms()  # sorting this column sorts by size
            if role == Qt.ItemDataRole.ToolTipRole:
                return row["smiles"]
            return None

        value = row[key]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)
        if role == SORT_ROLE:
            return value
        if role == Qt.ItemDataRole.TextAlignmentRole and key in NUMERIC_COLUMNS:
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.ForegroundRole and key == "status":
            return QColor("#4caf50") if value == "Active" else QColor("#9e9e9e")
        return None

    def set_highlight(self, query: Chem.Mol | None):
        self.highlight_query = query
        self.pixmap_cache.clear()
        # Tell views the images changed; they'll re-request only the visible ones.
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(len(self.rows) - 1, 0),
            [Qt.ItemDataRole.DecorationRole],
        )

    def set_highlighted_rows(self, rows: set[int]):
        changed = self.highlighted_rows ^ rows
        self.highlighted_rows = rows
        last_column = len(self.COLUMNS) - 1
        for row in changed:
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, last_column),
                [Qt.ItemDataRole.BackgroundRole],
            )

    def _thumbnail(self, row_index: int) -> QPixmap:
        if row_index not in self.pixmap_cache:
            mol = self.rows[row_index]["mol"]
            match = (
                mol.GetSubstructMatch(self.highlight_query)
                if self.highlight_query
                else ()
            )
            pixmap = QPixmap()
            pixmap.loadFromData(
                mol_to_png(mol, THUMBNAIL_SIZE.width(), THUMBNAIL_SIZE.height(), match)
            )
            self.pixmap_cache[row_index] = pixmap
        return self.pixmap_cache[row_index]


class CompoundFilterProxy(QSortFilterProxyModel):
    """Sits between model and view: decides which rows are visible and in what order."""

    def __init__(self):
        super().__init__()
        self.setSortRole(SORT_ROLE)
        self.text = ""
        self.series = None
        self.query = None
        self.value_ranges = (
            []
        )  # [(column key, min, max), ...]; a row must be inside all of them

    def set_filters(self, text="", series=None, query=None, value_ranges=()):
        self.beginFilterChange()
        self.text, self.series, self.query = text.lower(), series, query
        self.value_ranges = list(value_ranges)
        self.endFilterChange()

    def filterAcceptsRow(self, source_row, _parent):
        row = self.sourceModel().rows[source_row]
        if self.text and not any(
            self.text in row[k].lower() for k in ("id", "series", "smiles")
        ):
            return False
        if self.series and row["series"] != self.series:
            return False
        for key, low, high in self.value_ranges:
            if not low <= row[key] <= high:
                return False
        if self.query and not row["mol"].HasSubstructMatch(self.query):
            return False
        return True


class TableTab(QWidget):
    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.rows = build_dataset()
        self.model = CompoundTableModel(self.rows)
        self.proxy = CompoundFilterProxy()
        self.proxy.setSourceModel(self.model)

        # --- filter controls ------------------------------------------------------
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search ID, series or SMILES…")
        self.search_input.setClearButtonEnabled(True)

        self.substructure_input = QLineEdit()
        self.substructure_input.setPlaceholderText(
            "Substructure (SMILES/SMARTS), e.g. c1ccncc1 or C(F)(F)F"
        )
        self.substructure_input.setClearButtonEnabled(True)

        self.series_combo = QComboBox()
        self.series_combo.addItems(["All series", *SCAFFOLDS])

        self.range_column = QComboBox()
        self.range_column.addItems(NUMERIC_COLUMNS)
        self.range_min = QDoubleSpinBox()
        self.range_max = QDoubleSpinBox()
        for spin in (self.range_min, self.range_max):
            spin.setDecimals(2)
            spin.setRange(-1e6, 1e6)
            spin.setKeyboardTracking(
                False
            )  # apply when typing is done, not on every keystroke

        reset_button = QPushButton("Reset filters")
        reset_button.clicked.connect(self.reset_filters)
        self.count_label = QLabel()

        for signal in (
            self.search_input.textChanged,
            self.substructure_input.textChanged,
            self.series_combo.currentIndexChanged,
            self.range_min.valueChanged,
            self.range_max.valueChanged,
        ):
            signal.connect(self._apply_filters)
        self.range_column.currentTextChanged.connect(self._reset_range)

        text_row = QHBoxLayout()
        text_row.addWidget(self.search_input, stretch=1)
        text_row.addWidget(self.substructure_input, stretch=1)

        value_row = QHBoxLayout()
        value_row.addWidget(self.series_combo)
        value_row.addSpacing(16)
        value_row.addWidget(self.range_column)
        value_row.addWidget(QLabel("from"))
        value_row.addWidget(self.range_min)
        value_row.addWidget(QLabel("to"))
        value_row.addWidget(self.range_max)
        value_row.addWidget(reset_button)
        value_row.addStretch()
        value_row.addWidget(self.count_label)

        # --- table ---------------------------------------------------------------
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.setIconSize(THUMBNAIL_SIZE)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(THUMBNAIL_SIZE.height() + 6)
        self.table.horizontalHeader().setStretchLastSection(True)
        # Size text columns to fit. Skip the image column: measuring it would render every image.
        for column in range(1, self.model.columnCount()):
            self.table.resizeColumnToContents(column)
        self.table.setColumnWidth(0, THUMBNAIL_SIZE.width() + 10)
        self.table.setColumnWidth(3, 260)

        layout = QVBoxLayout(self)
        layout.addLayout(text_row)
        layout.addLayout(value_row)
        layout.addWidget(self.table)

        self._reset_range()

    def reset_filters(self):
        for widget in (self.search_input, self.substructure_input, self.series_combo):
            widget.blockSignals(True)
        self.search_input.clear()
        self.substructure_input.clear()
        self.series_combo.setCurrentIndex(0)
        for widget in (self.search_input, self.substructure_input, self.series_combo):
            widget.blockSignals(False)
        self._reset_range()

    def _reset_range(self):
        """Set the min/max boxes to the full range of the selected column (i.e. no filtering)."""
        values = [r[self.range_column.currentText()] for r in self.rows]
        for spin, value in [
            (self.range_min, min(values)),
            (self.range_max, max(values)),
        ]:
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self._apply_filters()

    def _apply_filters(self):
        query = self._parse_substructure()
        series = (
            self.series_combo.currentText()
            if self.series_combo.currentIndex() > 0
            else None
        )
        value_range = (
            self.range_column.currentText(),
            self.range_min.value(),
            self.range_max.value(),
        )

        self.proxy.set_filters(self.search_input.text(), series, query, [value_range])
        if query is not self.model.highlight_query:
            self.model.set_highlight(query)

        shown = self.proxy.rowCount()
        self.count_label.setText(f"Showing {shown} of {len(self.rows)}")
        self.status.emit(f"{shown} compounds match the current filters")

    def _parse_substructure(self) -> Chem.Mol | None:
        text = self.substructure_input.text().strip()
        query = Chem.MolFromSmarts(text) if text else None
        invalid = bool(text) and query is None
        self.substructure_input.setStyleSheet(
            "border: 1px solid #e53935;" if invalid else ""
        )
        # Reuse the current query object when it's unchanged (e.g. only the search box changed),
        # so the model doesn't throw away its cached images.
        current = self.model.highlight_query
        if (
            current is not None
            and query is not None
            and Chem.MolToSmarts(current) == Chem.MolToSmarts(query)
        ):
            return current
        return query
