from PySide6.QtCore import QByteArray, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from rdkit import Chem

from simmate.desktop.utilities import align_to_query, embed_3d, mol_to_svg
from simmate.desktop.widgets.compound_table import CompoundTableModel
from simmate.desktop.widgets.molecule_3d import Molecule3DView


class CompoundDetails(QWidget):
    """One compound shown in full: its structure plus every table column, transposed.

    The structure has a 2D tab and a 3D tab; the 3D conformer is only generated when
    asked for (then cached), so hovering through compounds stays fast.
    """

    def __init__(self, rows: list[dict]):
        super().__init__()
        self.rows = rows
        self.query: Chem.Mol | None = None
        self.current: int | None = None
        self.svg_cache: dict[int, bytes] = {}
        # row index -> 3D mol, or None when embedding failed
        self.mol_3d_cache: dict[int, Chem.Mol | None] = {}

        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setMinimumSize(240, 180)
        self.svg_widget.setStyleSheet("background: white;")

        # 3D tab: a "Generate 3D" page until this compound has a conformer
        self.generate_button = QPushButton("Generate 3D")
        self.generate_button.clicked.connect(self.generate_3d)
        self.generate_label = QLabel()
        self.generate_label.setWordWrap(True)
        self.generate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        generate_page = QWidget()
        generate_layout = QVBoxLayout(generate_page)
        generate_layout.addStretch()
        generate_layout.addWidget(
            self.generate_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        generate_layout.addWidget(self.generate_label)
        generate_layout.addStretch()

        self.viewer_3d = Molecule3DView()
        self.stack_3d = QStackedWidget()
        self.stack_3d.addWidget(generate_page)
        self.stack_3d.addWidget(self.viewer_3d)

        self.structure_tabs = QTabWidget()
        self.structure_tabs.addTab(self.svg_widget, "2D")
        self.structure_tabs.addTab(self.stack_3d, "3D")

        self.value_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        for header, key in CompoundTableModel.COLUMNS:
            if key == "structure":
                continue
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.value_labels[key] = label
            form.addRow(f"{header}:", label)
        self.value_labels["smiles"].setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.structure_tabs, stretch=1)
        layout.addLayout(form)

        self.show_row(None)

    def set_query(self, query: Chem.Mol | None):
        self.query = query
        self.svg_cache.clear()
        self.show_row(self.current)

    def show_row(self, index: int | None):
        self.current = index
        if index is None:
            self.title_label.setText("Hover or select a compound to see it here")
            self.svg_widget.load(QByteArray())
            self._show_3d()
            for label in self.value_labels.values():
                label.setText("-")
            return

        row = self.rows[index]
        if index not in self.svg_cache:
            mol, atoms, bonds = align_to_query(row["mol"], self.query)
            self.svg_cache[index] = mol_to_svg(mol, 400, 300, atoms, bonds)
        self.svg_widget.load(QByteArray(self.svg_cache[index]))
        # load() swaps in a new renderer config, so re-apply the aspect ratio.
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )

        self._show_3d()

        self.title_label.setText(f"{row['id']}  ({row['series']})")
        for key, label in self.value_labels.items():
            label.setText(str(row[key]))

    def generate_3d(self):
        """Embed the current compound in 3D and show it."""
        if self.current is None:
            return
        self.mol_3d_cache[self.current] = embed_3d(self.rows[self.current]["mol"])
        self._show_3d()

    def _show_3d(self):
        index = self.current
        if index is not None and self.mol_3d_cache.get(index) is not None:
            self.viewer_3d.show_mol(self.mol_3d_cache[index])
            self.stack_3d.setCurrentWidget(self.viewer_3d)
            return

        self.viewer_3d.show_mol(None)
        self.stack_3d.setCurrentIndex(0)
        self.generate_button.setEnabled(
            index is not None and index not in self.mol_3d_cache
        )
        if index is None:
            self.generate_label.setText("Select a compound first")
        elif index in self.mol_3d_cache:
            self.generate_label.setText("3D embedding failed for this compound")
        else:
            self.generate_label.setText("")
