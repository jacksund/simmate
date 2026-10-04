from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSize,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QColor, QPixmap
from rdkit import Chem

from simmate.desktop.utilities import align_to_query, mol_to_png

# Raw values for sorting (so 10 sorts after 9), separate from the displayed text.
SORT_ROLE = Qt.ItemDataRole.UserRole

NUMERIC_COLUMNS = ["pIC50", "solubility", "MolWt", "cLogP", "TPSA"]
THUMBNAIL_SIZE = QSize(180, 120)
HIGHLIGHT_COLOR = QColor("#fff3b0")


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

    def column(self, key: str) -> int:
        return [k for _, k in self.COLUMNS].index(key)

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
            mol, atoms, bonds = align_to_query(
                self.rows[row_index]["mol"], self.highlight_query
            )
            pixmap = QPixmap()
            pixmap.loadFromData(
                mol_to_png(
                    mol, THUMBNAIL_SIZE.width(), THUMBNAIL_SIZE.height(), atoms, bonds
                )
            )
            self.pixmap_cache[row_index] = pixmap
        return self.pixmap_cache[row_index]


class CompoundFilterProxy(QSortFilterProxyModel):
    """Sits between model and view: decides which rows are visible and in what order.

    Rows are filtered two ways, kept apart so changing one never clears the other:
    the user's filters (`set_filters`) and the plot's visible region (`set_view_ranges`).
    """

    def __init__(self):
        super().__init__()
        self.setSortRole(SORT_ROLE)
        self.text = ""
        self.series = None
        self.status = None
        self.query = None
        # [(column key, min, max), ...]; a row must be inside all of them
        self.value_ranges = []
        self.view_ranges = []

    def set_filters(
        self, text="", series=None, status=None, query=None, value_ranges=()
    ):
        self.beginFilterChange()
        self.text, self.series, self.status = text.lower(), series, status
        self.query = query
        self.value_ranges = list(value_ranges)
        self.endFilterChange()

    def set_view_ranges(self, view_ranges):
        self.beginFilterChange()
        self.view_ranges = list(view_ranges)
        self.endFilterChange()

    def accepts(self, row: dict, include_view: bool = True) -> bool:
        if self.text and not any(
            self.text in row[k].lower() for k in ("id", "series", "smiles")
        ):
            return False
        if self.series and row["series"] != self.series:
            return False
        if self.status and row["status"] != self.status:
            return False
        ranges = self.value_ranges + (self.view_ranges if include_view else [])
        for key, low, high in ranges:
            if not low <= row[key] <= high:
                return False
        if self.query is not None and not row["mol"].HasSubstructMatch(self.query):
            return False
        return True

    def filterAcceptsRow(self, source_row, _parent):
        return self.accepts(self.sourceModel().rows[source_row])
