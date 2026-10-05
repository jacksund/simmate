from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.widgets.button import PrimaryButton
from simmate.desktop.widgets.compound_table import NUMERIC_COLUMNS, CompoundTableModel
from simmate.desktop.widgets.inputs import input_style, style_combo
from simmate.desktop.widgets.ketcher import KetcherWidget
from simmate.desktop.widgets.title_bar import MUTED_COLOR

FILTER_STYLE = f"""
#panelTitle {{ color: {MUTED_COLOR}; font-weight: bold; }}
#rangeSep {{ color: palette(placeholder-text); }}
/* see-through, so the window shows behind the panel like the rest of the app */
#filterScroll, #filterContent {{ background: transparent; }}
"""


class FilterPanel(QWidget):
    """The dashboard's filter column: a substructure sketcher with column filters below.

    `filters_changed` fires whenever anything changes; read the new state with `filters()`.
    """

    filters_changed = Signal()

    SKETCHER_HEIGHT = 380

    def __init__(self, rows: list[dict]):
        super().__init__()
        self.rows = rows
        self.query = None
        self.setStyleSheet(FILTER_STYLE + input_style())

        # --- header -------------------------------------------------------------------
        title = QLabel("Filters", objectName="panelTitle")
        font = title.font()
        font.setPointSizeF(font.pointSizeF() * 1.3)
        title.setFont(font)
        reset_button = PrimaryButton("Reset filters", muted=True)
        reset_button.setToolTip("Clear the sketch and every filter below it")
        reset_button.clicked.connect(self.reset_filters)

        header = QHBoxLayout()
        header.addWidget(title, stretch=1)
        header.addWidget(reset_button)

        # --- substructure sketcher ----------------------------------------------------
        self.sketcher = KetcherWidget()
        self.sketcher.setFixedHeight(self.SKETCHER_HEIGHT)
        self.sketcher.mol_changed.connect(self._on_query_changed)

        # --- column filters -------------------------------------------------------------
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ID, series or SMILES…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filters_changed)

        self.series_combo = QComboBox()
        self.series_combo.addItems(["All", *sorted({r["series"] for r in self.rows})])
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Active", "Inactive"])
        for combo in (self.series_combo, self.status_combo):
            style_combo(combo)
            combo.currentIndexChanged.connect(self.filters_changed)

        # A grid rather than a QFormLayout, which won't center labels on taller fields.
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        form.setColumnStretch(1, 1)

        def add_row(label: str, field: QWidget):
            row = form.rowCount()
            form.addWidget(QLabel(label), row, 0, Qt.AlignmentFlag.AlignVCenter)
            form.addWidget(field, row, 1)

        add_row("Search", self.search_input)
        add_row("Series", self.series_combo)
        add_row("Status", self.status_combo)

        headers = {key: header for header, key in CompoundTableModel.COLUMNS}
        self.range_inputs: dict[str, tuple[QDoubleSpinBox, QDoubleSpinBox]] = {}
        for key in NUMERIC_COLUMNS:
            spins = (QDoubleSpinBox(), QDoubleSpinBox())
            range_row = QWidget()
            range_layout = QHBoxLayout(range_row)
            range_layout.setContentsMargins(0, 0, 0, 0)
            range_layout.setSpacing(6)
            for i, spin in enumerate(spins):
                spin.setDecimals(2)
                spin.setRange(-1e6, 1e6)
                # arrow keys and the mouse wheel still step the value
                spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
                # apply when typing is done, not on every keystroke
                spin.setKeyboardTracking(False)
                spin.valueChanged.connect(self.filters_changed)
                if i:
                    range_layout.addWidget(QLabel("to", objectName="rangeSep"))
                range_layout.addWidget(spin, stretch=1)
            self.range_inputs[key] = spins
            add_row(headers.get(key, key), range_row)

        # --- layout -------------------------------------------------------------------
        content = QWidget(objectName="filterContent")
        content_layout = QVBoxLayout(content)
        # breathing room from the window's edges and the pull tab's line (right)
        content_layout.setContentsMargins(8, 8, 12, 8)
        content_layout.addLayout(header)
        content_layout.addSpacing(8)
        content_layout.addWidget(self.sketcher)
        content_layout.addSpacing(20)
        content_layout.addLayout(form)
        content_layout.addStretch()

        # Scrolls rather than squashing the fixed-height sketcher on short windows.
        scroll = QScrollArea(objectName="filterScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self._reset_form()

    def filters(self) -> dict:
        """The current filters, as keyword arguments for `CompoundFilterProxy.set_filters`."""
        return dict(
            text=self.search_input.text(),
            series=(
                self.series_combo.currentText()
                if self.series_combo.currentIndex()
                else None
            ),
            status=(
                self.status_combo.currentText()
                if self.status_combo.currentIndex()
                else None
            ),
            query=self.query,
            value_ranges=[
                (key, low.value(), high.value())
                for key, (low, high) in self.range_inputs.items()
            ],
        )

    def reset_filters(self):
        """Clear the sketch and every column filter."""
        # The sketcher reports its (now empty) canvas back through `mol_changed`.
        self.sketcher.clear()
        self._reset_form()

    def _reset_form(self):
        widgets = [self.search_input, self.series_combo, self.status_combo]
        for spins in self.range_inputs.values():
            widgets.extend(spins)
        for widget in widgets:
            widget.blockSignals(True)

        self.search_input.clear()
        self.series_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        # Set each min/max box to the full range of its column (i.e. no filtering).
        for key, (low, high) in self.range_inputs.items():
            values = [r[key] for r in self.rows]
            low.setValue(min(values))
            high.setValue(max(values))

        for widget in widgets:
            widget.blockSignals(False)
        self.filters_changed.emit()

    def _on_query_changed(self, query):
        self.query = query
        self.filters_changed.emit()
