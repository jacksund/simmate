from functools import cached_property

import numpy as np
import polars
from PySide6.QtCore import (
    QAbstractTableModel,
    QByteArray,
    QModelIndex,
    QRectF,
    QSize,
    QSizeF,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop import theme
from simmate.desktop.theme import rgba, tint
from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.inputs import StyledCheckBox, line_pen, polyline
from simmate.toolkit import Molecule
from simmate.toolkit.dataframes import MoleculeDataFrame

# Raw values for sorting (so 10 sorts after 9), separate from the displayed text.
SORT_ROLE = Qt.ItemDataRole.UserRole

NUMERIC_COLUMNS = ["pIC50", "solubility", "MolWt", "cLogP", "TPSA"]
THUMBNAIL_SIZE = QSize(180, 120)  # the starting size; it follows the column's width
MIN_THUMBNAIL_WIDTH = 60  # so images stay legible when the column is squeezed
THUMBNAIL_PADDING = 10  # px of column width beside the image
# Every other row is a shade darker than the window (as rgba, so it works over a
# light or dark background).
STRIPE_COLOR = "rgba(0, 0, 0, 12)"


def table_style() -> str:
    """Bordered and rounded like the inputs, but on the window's own background (the
    rows, header and scroll bars alike): tinted headers, striped rows with no grid,
    and a slim scroll bar.

    Selection is the primary color at 25%, between the hover and the full color.
    """
    return f"""
QTableView {{
    background: palette(window); alternate-background-color: {STRIPE_COLOR};
    border: 1px solid palette(mid); border-radius: 6px;
    gridline-color: transparent; outline: none;
    selection-background-color: {rgba(theme.PRIMARY_COLOR, "25%")};
    selection-color: palette(text);
}}
/* room between columns, which have no grid lines to split them */
QTableView::item {{ padding: 0 8px; }}
QAbstractScrollArea::corner {{ background: transparent; }}
/* the tint goes over the window color, which the header itself paints */
QHeaderView {{ background: palette(window); border-top-left-radius: 6px;
    border-top-right-radius: 6px; }}
QHeaderView::section {{
    background: {rgba(theme.PRIMARY_COLOR, theme.HOVER_ALPHA)};
    color: palette(text); font-weight: 600;
    border: none; border-bottom: 1px solid palette(mid);
    padding: 8px;
}}
/* the header's first and last cells follow the card's rounded corners */
QHeaderView::section:first {{ border-top-left-radius: 6px; }}
QHeaderView::section:last {{ border-top-right-radius: 6px; }}
QHeaderView::section:hover {{ color: {theme.PRIMARY_COLOR}; }}
/* hidden: `_SortHeader` draws the sort arrow beside its label instead */
QHeaderView::up-arrow, QHeaderView::down-arrow {{ image: none; width: 0; }}
{scroll_bar_style()}"""


def scroll_bar_style() -> str:
    """Slim, rounded scroll bars on a transparent track, with no arrow buttons."""
    return f"""
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: palette(mid); border-radius: 3px; }}
QScrollBar::handle:vertical {{ min-height: 30px; }}
QScrollBar::handle:horizontal {{ min-width: 30px; }}
QScrollBar::handle:hover {{ background: {theme.MUTED_COLOR}; }}
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

    def __init__(self, mdf: MoleculeDataFrame):
        super().__init__()
        self.mdf = mdf
        # Hovered rows, in line with the website (see website/core/static/css/simmate.css):
        # matches --bs-primary-bg-subtle (the primary color at 10% opacity).
        self.highlight_color = tint(theme.PRIMARY_COLOR, theme.HIGHLIGHT_ALPHA)
        self.highlight_query: Molecule | None = None
        self.thumbnail_size = THUMBNAIL_SIZE
        # By row index. Drawing the SVG (RDKit) is the slow part and doesn't depend on
        # the display size, so a resize only re-rasterizes the cached SVGs.
        self.svg_cache: dict[int, bytes] = {}
        self.pixmap_cache: dict[int, QPixmap] = {}
        self.highlighted_rows: set[int] = set()  # e.g. rows whose plot point is hovered

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self.mdf.df.height

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
        row = index.row()
        key = self.COLUMNS[index.column()][1]

        # Qt asks for many roles per cell on every paint; answer the cheap ones
        # before touching the dataframe.
        if role == Qt.ItemDataRole.BackgroundRole:
            return self.highlight_color if row in self.highlighted_rows else None

        if key == "structure":
            if role == Qt.ItemDataRole.DecorationRole:
                return self._thumbnail(row)
            if role == SORT_ROLE:
                # sorting this column sorts by size
                return self._heavy_atom_counts[row]
            if role == Qt.ItemDataRole.ToolTipRole:
                return self._columns["smiles"][row]
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if key in NUMERIC_COLUMNS:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        if role == Qt.ItemDataRole.ForegroundRole and key == "status":
            active = self._columns[key][row] == "Active"
            return QColor("#4caf50") if active else QColor("#9e9e9e")
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._columns[key][row])
        if role == SORT_ROLE:
            return self._columns[key][row]
        return None

    # Plain lists, computed once: Qt asks for cells on every paint, and sorting
    # asks for every row's key many times over.
    @cached_property
    def _columns(self) -> dict[str, list]:
        return {key: self.mdf.df[key].to_list() for _, key in self.COLUMNS[1:]}

    @cached_property
    def _heavy_atom_counts(self) -> list[int]:
        return [m.num_atoms_heavy for m in self.mdf.df["molecule_obj"]]

    def column(self, key: str) -> int:
        return [k for _, k in self.COLUMNS].index(key)

    def set_highlight(self, query: Molecule | None):
        self.highlight_query = query
        self.svg_cache.clear()
        self.pixmap_cache.clear()
        self._images_changed()

    def set_thumbnail_size(self, size: QSize):
        if size == self.thumbnail_size:
            return
        self.thumbnail_size = size
        self.pixmap_cache.clear()
        self._images_changed()

    def _images_changed(self):
        # Tell views the images changed; they'll re-request only the visible ones.
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, 0),
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
            if row_index not in self.svg_cache:
                molecule = self.mdf.df["molecule_obj"][row_index]
                # always drawn at THUMBNAIL_SIZE, then scaled as a vector below
                self.svg_cache[row_index] = molecule.draw(
                    "svg",
                    size=(THUMBNAIL_SIZE.width(), THUMBNAIL_SIZE.height()),
                    highlight_query=self.highlight_query,
                )
            size = self.thumbnail_size
            # Paint the vector image at the screen's real resolution. A PNG at
            # this size gets stretched, and so pixelated, under display
            # scaling (e.g. 125%, common on Windows).
            ratio = QGuiApplication.instance().devicePixelRatio()
            pixmap = QPixmap(size * ratio)
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            # explicit bounds: by default the renderer fills the pixmap's size in
            # device pixels, which the ratio then scales up a second time
            bounds = QRectF(0, 0, size.width(), size.height())
            QSvgRenderer(QByteArray(self.svg_cache[row_index])).render(painter, bounds)
            painter.end()
            self.pixmap_cache[row_index] = pixmap
        return self.pixmap_cache[row_index]


class CompoundFilterProxy(QSortFilterProxyModel):
    """Sits between model and view: decides which rows are visible and in what order.

    Rows are filtered two ways, kept apart so changing one never clears the other:
    the user's filters (`set_filters`) and the plot's visible region (`set_view_ranges`).
    Each is evaluated over the whole dataframe at once, into a mask of rows to keep.
    """

    def __init__(self, model: CompoundTableModel):
        super().__init__()
        # By row index: which rows pass the user's filters / sit in the plot's view.
        self.passing = np.ones(model.rowCount(), dtype=bool)
        self.in_view = self.passing.copy()
        self.setSourceModel(model)
        self.setSortRole(SORT_ROLE)
        # The last substructure query and its matches, by row index. Only the
        # sketcher changes the query, so other filter edits reuse the search.
        self._query = None
        self._query_matches = None

    @property
    def mdf(self) -> MoleculeDataFrame:
        return self.sourceModel().mdf

    def set_filters(
        self, text="", series=None, status=None, query=None, value_ranges=()
    ):
        checks = [_range_check(key, low, high) for key, low, high in value_ranges]
        if text:
            checks.append(
                polars.any_horizontal(
                    polars.col(key)
                    .str.to_lowercase()
                    .str.contains(text.lower(), literal=True)
                    for key in ("id", "series", "smiles")
                )
            )
        if series:
            checks.append(polars.col("series") == series)
        if status:
            checks.append(polars.col("status") == status)
        passing = self._mask(checks)
        if query is not None:
            passing &= self._substructure_matches(query)

        self.beginFilterChange()
        self.passing = passing
        self.endFilterChange()

    def set_view_ranges(self, view_ranges):
        in_view = self._mask([_range_check(*r) for r in view_ranges])
        self.beginFilterChange()
        self.in_view = in_view
        self.endFilterChange()

    def _substructure_matches(self, query: Molecule) -> np.ndarray:
        if query is not self._query:
            self._query = query
            self._query_matches = np.zeros(self.mdf.df.height, dtype=bool)
            self._query_matches[self.mdf.get_substructure_matches(query)] = True
        return self._query_matches

    def _mask(self, checks: list[polars.Expr]) -> np.ndarray:
        """Evaluate `checks` over every row: True where a row passes all of them."""
        df = self.mdf.df
        if not checks:
            return np.ones(df.height, dtype=bool)
        return df.select(polars.all_horizontal(checks)).to_series().to_numpy().copy()

    def filterAcceptsRow(self, source_row, _parent):
        return bool(self.passing[source_row] and self.in_view[source_row])


def _range_check(key: str, low: float, high: float) -> polars.Expr:
    return polars.col(key).is_between(low, high)


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
        # the same light tint of the primary color that the stylesheet gives sections
        self.color = tint(theme.PRIMARY_COLOR, theme.HOVER_ALPHA)
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
            painter.fillRect(strip, self.color)
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
        chevron = polyline([(left + x, top + y) for x, y in points])

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(line_pen(theme.PRIMARY_COLOR))
        painter.drawPath(chevron)
        painter.restore()


class CompoundTable(QTableView):
    """The dataset as a sortable, read-only table, one row per compound with its image."""

    def __init__(self, proxy: CompoundFilterProxy):
        super().__init__()
        model = proxy.sourceModel()
        self.setHorizontalHeader(_SortHeader())
        self.setModel(proxy)
        self.setStyleSheet(table_style())
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
        # Size text columns to fit. Skip the image column (measuring it would render
        # every image) and hidden ones (measuring them is wasted work).
        for column in range(1, model.columnCount()):
            if not self.isColumnHidden(column):
                self.resizeColumnToContents(column)
        self.setColumnWidth(0, THUMBNAIL_SIZE.width() + THUMBNAIL_PADDING)
        # the images (and so the rows) grow and shrink with the column's width
        header.sectionResized.connect(self._on_section_resized)
        self.setMouseTracking(True)  # needed for the `entered` (hover) signal

    def _on_section_resized(self, column: int, _old_width: int, new_width: int):
        model = self.model().sourceModel()
        if column != model.column("structure"):
            return
        width = max(new_width - THUMBNAIL_PADDING, MIN_THUMBNAIL_WIDTH)
        # keep THUMBNAIL_SIZE's aspect ratio
        height = round(width * THUMBNAIL_SIZE.height() / THUMBNAIL_SIZE.width())
        size = QSize(width, height)
        self.setIconSize(size)
        self.verticalHeader().setDefaultSectionSize(height + 6)
        model.set_thumbnail_size(size)

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


class ColumnChooser(QWidget):
    """A checklist of a `CompoundTable`'s columns, to show or hide each one.

    The last visible column can't be unchecked, so the table never goes empty;
    likewise "Deselect all" leaves the first column showing.
    """

    def __init__(self, table: CompoundTable):
        super().__init__()
        self.table = table
        model = table.model().sourceModel()
        # Columns hidden at startup were never sized; size them when first shown.
        self.unsized = {
            i for i in range(1, model.columnCount()) if table.isColumnHidden(i)
        }
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        select_all = PrimaryButton("Select all", muted=True)
        select_all.clicked.connect(lambda: self._set_all(True))
        deselect_all = PrimaryButton("Deselect all", muted=True)
        deselect_all.clicked.connect(lambda: self._set_all(False))
        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        buttons.addWidget(select_all)
        buttons.addWidget(deselect_all)
        layout.addLayout(buttons)

        self.checkboxes: list[StyledCheckBox] = []
        for column, (label, _) in enumerate(model.COLUMNS):
            checkbox = StyledCheckBox(label)
            checkbox.setChecked(not table.isColumnHidden(column))
            checkbox.toggled.connect(
                lambda on, column=column: self._set_shown(column, on)
            )
            layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
        self._update_enabled()

    def _set_shown(self, column: int, shown: bool):
        self.table.setColumnHidden(column, not shown)
        if shown and column in self.unsized:
            self.unsized.discard(column)
            self.table.resizeColumnToContents(column)
        self._update_enabled()

    def _set_all(self, shown: bool):
        # the first column always stays, so the table never goes empty
        self.checkboxes[0].setChecked(True)
        for checkbox in self.checkboxes[1:]:
            checkbox.setChecked(shown)

    def _update_enabled(self):
        checked = [box for box in self.checkboxes if box.isChecked()]
        for box in self.checkboxes:
            box.setEnabled(len(checked) > 1 or not box.isChecked())
