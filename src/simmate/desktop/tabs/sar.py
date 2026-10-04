import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from simmate.desktop.example_data.sar import CORE, PROPERTIES, build_dataset
from simmate.desktop.utilities import PlotToolbar, mol_to_svg


class SarTab(QWidget):
    """Scatter plot of a compound series; hovering a point shows its structure."""

    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.rows = build_dataset()
        self.svg_cache: dict[int, bytes] = {}

        # --- plot -------------------------------------------------------------
        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
        for combo, default in [(self.x_combo, "cLogP"), (self.y_combo, "pIC50")]:
            combo.addItems(PROPERTIES)
            combo.setCurrentText(default)
            combo.currentTextChanged.connect(self._update_axes)

        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)

        # Color every point by potency so trends are visible regardless of the chosen axes.
        pic50 = np.array([r["pIC50"] for r in self.rows])
        cmap = pg.colormap.get("viridis")
        colors = cmap.map((pic50 - pic50.min()) / np.ptp(pic50), mode="qcolor")
        self.brushes = [pg.mkBrush(c) for c in colors]

        self.scatter = pg.ScatterPlotItem(
            size=11,
            pen=pg.mkPen(None),
            hoverable=True,
            hoverSize=18,
            hoverPen=pg.mkPen("w", width=2),
            tip=None,  # we show our own structure panel instead of a text tooltip
        )
        self.scatter.sigHovered.connect(self._on_hover)
        self.plot.addItem(self.scatter)

        color_bar = pg.ColorBarItem(
            values=(pic50.min(), pic50.max()),
            colorMap=cmap,
            label="pIC50",
            interactive=False,
        )
        self.plot.getPlotItem().layout.addItem(color_bar, 2, 5)

        axis_controls = QHBoxLayout()
        axis_controls.addWidget(QLabel("X:"))
        axis_controls.addWidget(self.x_combo)
        axis_controls.addWidget(QLabel("Y:"))
        axis_controls.addWidget(self.y_combo)
        axis_controls.addStretch()
        axis_controls.addWidget(PlotToolbar(self.plot))

        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        plot_layout.addLayout(axis_controls)
        plot_layout.addWidget(self.plot)

        # --- structure panel ----------------------------------------------------
        self.svg_widget = QSvgWidget()
        self.svg_widget.setMinimumSize(300, 240)
        self.svg_widget.setStyleSheet("background: white;")

        self.title_label = QLabel("Hover a point to see its structure")
        self.title_label.setWordWrap(True)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.prop_labels = {name: QLabel("-") for name in ["SMILES", *PROPERTIES]}
        self.prop_labels["SMILES"].setWordWrap(True)
        self.prop_labels["SMILES"].setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        props = QFormLayout()
        for name, label in self.prop_labels.items():
            props.addRow(f"{name}:", label)

        detail_panel = QWidget()
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.addWidget(self.title_label)
        detail_layout.addWidget(self.svg_widget, stretch=1)
        detail_layout.addLayout(props)

        splitter = QSplitter()
        splitter.addWidget(plot_panel)
        splitter.addWidget(detail_panel)
        splitter.setSizes([600, 350])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self._update_axes()

    def _update_axes(self):
        x_name, y_name = self.x_combo.currentText(), self.y_combo.currentText()
        # setData() rebuilds the points, so pass the per-point styling along with them.
        self.scatter.setData(
            x=[r[x_name] for r in self.rows],
            y=[r[y_name] for r in self.rows],
            brush=self.brushes,
            data=list(range(len(self.rows))),  # each point remembers its row index
        )
        self.plot.setLabel("bottom", x_name)
        self.plot.setLabel("left", y_name)
        self.plot.autoRange()

    def _on_hover(self, _item, points, _event):
        # Empty while the cursor is between points; keep the last structure on screen.
        if len(points) == 0:
            return
        self.show_compound(points[0].data())

    def show_compound(self, index: int):
        row = self.rows[index]
        if index not in self.svg_cache:
            core_atoms = row["mol"].GetSubstructMatch(CORE)
            self.svg_cache[index] = mol_to_svg(
                row["mol"], 400, 320, highlight_atoms=core_atoms
            )
        self.svg_widget.load(QByteArray(self.svg_cache[index]))
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )

        self.title_label.setText(f"{row['id']}  ({row['label']})")
        self.prop_labels["SMILES"].setText(row["smiles"])
        for name in PROPERTIES:
            self.prop_labels[name].setText(str(row[name]))
        self.status.emit(f"{row['id']}: pIC50 {row['pIC50']}")
