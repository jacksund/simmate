from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.widgets.compound_table import NUMERIC_COLUMNS
from simmate.desktop.widgets.ketcher import KetcherWidget


class FilterPanel(QWidget):
    """The dashboard's filter column: a substructure sketcher with column filters below.

    `filters_changed` fires whenever anything changes; read the new state with `filters()`.
    """

    filters_changed = Signal()

    def __init__(self, rows: list[dict]):
        super().__init__()
        self.rows = rows
        self.query = None

        # --- substructure sketcher ----------------------------------------------------
        self.sketcher = KetcherWidget()
        self.sketcher.mol_changed.connect(self._on_query_changed)
        clear_button = QPushButton("Clear sketch")
        clear_button.clicked.connect(self.sketcher.clear)
        self.query_label = QLabel()
        self.query_label.setWordWrap(True)

        sketch_footer = QHBoxLayout()
        sketch_footer.addWidget(self.query_label, stretch=1)
        sketch_footer.addWidget(clear_button)

        # The sketcher's white canvas blends into the panel, so frame it.
        sketch_frame = QFrame()
        sketch_frame.setObjectName("sketchFrame")
        sketch_frame.setStyleSheet(
            "#sketchFrame { border: 1px solid palette(mid); border-radius: 4px;"
            " background: palette(mid); }"
        )
        frame_layout = QVBoxLayout(sketch_frame)
        frame_layout.setContentsMargins(1, 1, 1, 1)
        frame_layout.addWidget(self.sketcher)

        sketch_panel = QWidget()
        sketch_layout = QVBoxLayout(sketch_panel)
        sketch_layout.setContentsMargins(0, 0, 0, 0)
        sketch_layout.addWidget(QLabel("<b>Substructure</b>"))
        sketch_layout.addWidget(sketch_frame, stretch=1)
        sketch_layout.addLayout(sketch_footer)

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
            combo.currentIndexChanged.connect(self.filters_changed)

        form = QFormLayout()
        form.addRow("Search:", self.search_input)
        form.addRow("Series:", self.series_combo)
        form.addRow("Status:", self.status_combo)

        self.range_inputs: dict[str, tuple[QDoubleSpinBox, QDoubleSpinBox]] = {}
        for key in NUMERIC_COLUMNS:
            spins = (QDoubleSpinBox(), QDoubleSpinBox())
            range_row = QHBoxLayout()
            for i, spin in enumerate(spins):
                spin.setDecimals(2)
                spin.setRange(-1e6, 1e6)
                # apply when typing is done, not on every keystroke
                spin.setKeyboardTracking(False)
                spin.valueChanged.connect(self.filters_changed)
                if i:
                    range_row.addWidget(QLabel("to"))
                range_row.addWidget(spin, stretch=1)
            self.range_inputs[key] = spins
            form.addRow(f"{key}:", range_row)

        reset_button = QPushButton("Reset filters")
        reset_button.clicked.connect(self.reset_filters)

        filters_panel = QWidget()
        filters_layout = QVBoxLayout(filters_panel)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.addWidget(QLabel("<b>Filters</b>"))
        filters_layout.addLayout(form)
        filters_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignRight)
        filters_layout.addStretch()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(sketch_panel)
        splitter.addWidget(filters_panel)
        splitter.setSizes([450, 350])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.reset_filters()
        self._update_query_label()

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
        """Clear every column filter (the sketch is left alone; it has its own button)."""
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
        self._update_query_label()
        self.filters_changed.emit()

    def _update_query_label(self):
        if self.query is None:
            self.query_label.setText("Draw a structure to filter by substructure")
            return
        matches = sum(r["mol"].HasSubstructMatch(self.query) for r in self.rows)
        self.query_label.setText(f"{matches} of {len(self.rows)} compounds match")
