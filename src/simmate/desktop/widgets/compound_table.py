from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPointF,
    QSize,
    QSizeF,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QTableView,
)
from rdkit import Chem

from simmate.desktop.utilities import align_to_query, mol_to_png
from simmate.desktop.widgets.title_bar import (
    MUTED_COLOR,
    PRIMARY_COLOR,
)

# Raw values for sorting (so 10 sorts after 9), separate from the displayed text.
SORT_ROLE = Qt.ItemDataRole.UserRole

NUMERIC_COLUMNS = ["pIC50", "solubility", "MolWt", "cLogP", "TPSA"]
THUMBNAIL_SIZE = QSize(180, 120)
# Row colors, in line with the website (see website/core/static/css/simmate.css).
# Hover matches --bs-primary-bg-subtle (the primary teal at 10% opacity).
HIGHLIGHT_COLOR = QColor(0, 148, 133, 26)
# Selection is the same teal at 25%, between the hover and the full primary color.
SELECTION_COLOR = "rgba(0, 148, 133, 25%)"
# Header cells get a light tint of the primary color (as rgba, so it works over a
# light or dark background).
HEADER_COLOR = QColor(0, 148, 133, 30)
HEADER_RGBA = "rgba({}, {}, {}, {})".format(*HEADER_COLOR.getRgb())
# Every other row is a shade darker than the window (as rgba, for the same reason).
STRIPE_COLOR = "rgba(0, 0, 0, 12)"
# Bordered and rounded like the inputs, but on the window's own background (the
# rows, header and scroll bars alike): tinted headers, striped rows with no grid,
# and a slim scroll bar.
TABLE_STYLE = f"""
QTableView {{
    background: palette(window); alternate-background-color: {STRIPE_COLOR};
    border: 1px solid palette(mid); border-radius: 6px;
    gridline-color: transparent; outline: none;
    selection-background-color: {SELECTION_COLOR}; selection-color: palette(text);
}}
/* room between columns, which have no grid lines to split them */
QTableView::item {{ padding: 0 8px; }}
QAbstractScrollArea::corner {{ background: transparent; }}
/* the tint goes over the window color, which the header itself paints */
QHeaderView {{ background: palette(window); border-top-left-radius: 6px;
    border-top-right-radius: 6px; }}
QHeaderView::section {{
    background: {HEADER_RGBA}; color: palette(text); font-weight: 600;
    border: none; border-bottom: 1px solid palette(mid);
    padding: 8px;
}}
/* the header's first and last cells follow the card's rounded corners */
QHeaderView::section:first {{ border-top-left-radius: 6px; }}
QHeaderView::section:last {{ border-top-right-radius: 6px; }}
QHeaderView::section:hover {{ color: {PRIMARY_COLOR}; }}
/* hidden: `_SortHeader` draws the sort arrow beside its label instead */
QHeaderView::up-arrow, QHeaderView::down-arrow {{ image: none; width: 0; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: palette(mid); border-radius: 3px; }}
QScrollBar::handle:vertical {{ min-height: 30px; }}
QScrollBar::handle:horizontal {{ min-width: 30px; }}
QScrollBar::handle:hover {{ background: {MUTED_COLOR}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


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
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section][0]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            # over its values: numbers on the right, everything else on the left
            horizontal = (
                Qt.AlignmentFlag.AlignRight
                if self.COLUMNS[section][1] in NUMERIC_COLUMNS
                else Qt.AlignmentFlag.AlignLeft
            )
            return horizontal | Qt.AlignmentFlag.AlignVCenter
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


class _SortHeader(QHeaderView):
    """Column headers with a small chevron to the right of the sorted column's label.

    The stylesheet's own arrow sits at the section's edge, where it covers
    right-aligned labels. Instead, every section has room for the arrow, and a
    right-aligned label moves over to make way for it while it's sorted.
    """

    GAP = 5  # px between the label and the arrow
    ARROW = QSizeF(8, 4.5)
    PADDING = 8  # the section's side padding in the stylesheet

    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        # Unlike the table's default header, a new one ignores clicks (i.e. sorting).
        self.setSectionsClickable(True)

    def _arrow_space(self) -> int:
        return round(self.GAP + self.ARROW.width())

    def sectionSizeFromContents(self, logical_index):
        size = super().sectionSizeFromContents(logical_index)
        return size + QSize(self._arrow_space(), 0)

    def paintSection(self, painter, rect, logical_index):
        if (
            not self.isSortIndicatorShown()
            or logical_index != self.sortIndicatorSection()
        ):
            super().paintSection(painter, rect, logical_index)
            return

        model = self.model()
        label = model.headerData(logical_index, self.orientation())
        alignment = model.headerData(
            logical_index, self.orientation(), Qt.ItemDataRole.TextAlignmentRole
        )
        space = self._arrow_space()
        if alignment & Qt.AlignmentFlag.AlignRight:
            # Draw the section short, so its label ends before the arrow, then
            # finish the background and bottom line under the arrow.
            super().paintSection(painter, rect.adjusted(0, 0, -space, 0), logical_index)
            strip = rect.adjusted(rect.width() - space, 0, 0, 0)
            painter.fillRect(strip, HEADER_COLOR)
            painter.setPen(self.palette().color(QPalette.ColorRole.Mid))
            painter.drawLine(strip.bottomLeft(), strip.bottomRight())
            left = rect.right() - self.PADDING - self.ARROW.width()
        else:
            super().paintSection(painter, rect, logical_index)
            font = painter.font()
            font.setWeight(QFont.Weight.DemiBold)  # as styled, for an accurate width
            label_width = QFontMetrics(font).horizontalAdvance(label)
            left = rect.left() + self.PADDING + label_width + self.GAP

        top = rect.center().y() - self.ARROW.height() / 2 + 1
        width, height = self.ARROW.width(), self.ARROW.height()
        if self.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder:
            points = [(0, height), (width / 2, 0), (width, height)]  # pointing up
        else:
            points = [(0, 0), (width / 2, height), (width, 0)]
        chevron = QPainterPath(QPointF(left + points[0][0], top + points[0][1]))
        for x, y in points[1:]:
            chevron.lineTo(left + x, top + y)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(PRIMARY_COLOR), 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(chevron)
        painter.restore()


class CompoundTable(QTableView):
    """The dataset as a sortable, read-only table, one row per compound with its image."""

    def __init__(self, proxy: CompoundFilterProxy):
        super().__init__()
        model = proxy.sourceModel()
        self.setHorizontalHeader(_SortHeader())
        self.setModel(proxy)
        self.setStyleSheet(TABLE_STYLE)
        self.setFrameShape(QFrame.Shape.NoFrame)  # the stylesheet draws the border
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.sortByColumn(model.column("pIC50"), Qt.SortOrder.DescendingOrder)
        self.setIconSize(THUMBNAIL_SIZE)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setWordWrap(False)
        # Smooth scrolling, rather than jumping a whole (tall) row at a time.
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(THUMBNAIL_SIZE.height() + 6)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setHighlightSections(False)  # no bold header over a selected row
        header.setCursor(Qt.CursorShape.PointingHandCursor)  # click to sort
        for key in ("smiles", "tested"):
            self.setColumnHidden(model.column(key), True)
        # Size text columns to fit. Skip the image column: measuring it would render every image.
        for column in range(1, model.columnCount()):
            self.resizeColumnToContents(column)
        self.setColumnWidth(0, THUMBNAIL_SIZE.width() + 10)
        self.setMouseTracking(True)  # needed for the `entered` (hover) signal

    def wheelEvent(self, event):
        # Shift+scroll moves sideways, as in most web tables. Qt otherwise uses Alt.
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Touchpads give exact pixels. Some systems already turn a shifted
            # wheel sideways, so take whichever direction moved.
            delta = event.pixelDelta()
            if delta.isNull():
                delta = event.angleDelta()  # 120 per notch, i.e. 120px
            bar = self.horizontalScrollBar()
            bar.setValue(bar.value() - (delta.y() or delta.x()))
            event.accept()
            return
        super().wheelEvent(event)
