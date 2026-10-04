import random

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolDescriptors

from simmate.desktop.utilities import mol_to_svg

# RDKit prints parse errors to stderr; we report them in the UI instead.
RDLogger.DisableLog("rdApp.*")

EXAMPLES = {
    "caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "aspirin": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "serotonin": "C1=CC2=C(C=C1O)C(=CN2)CCN",
    "penicillin G": "CC1(C(N2C(S1)C(C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C",
    "dopamine": "C1=CC(=C(C=C1CCN)O)O",
}


class MoleculeTab(QWidget):
    """Type a SMILES string, get a 2D structure drawing (RDKit -> SVG -> Qt)."""

    status = Signal(str)

    def __init__(self):
        super().__init__()

        self.smiles_input = QLineEdit(EXAMPLES["caffeine"])
        self.smiles_input.setPlaceholderText("Enter a SMILES string, e.g. CCO")
        self.smiles_input.returnPressed.connect(self.draw)

        draw_button = QPushButton("Draw")
        draw_button.clicked.connect(self.draw)
        random_button = QPushButton("Random example")
        random_button.clicked.connect(self._random_example)

        self.svg_widget = QSvgWidget()
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )
        self.svg_widget.setStyleSheet("background: white;")

        controls = QHBoxLayout()
        controls.addWidget(self.smiles_input)
        controls.addWidget(draw_button)
        controls.addWidget(random_button)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.svg_widget, stretch=1)

        self.draw()

    def draw(self):
        smiles = self.smiles_input.text().strip()
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            self.status.emit(f"Invalid SMILES: {smiles!r}")
            return

        self.svg_widget.load(QByteArray(mol_to_svg(mol)))
        # load() swaps in a new renderer config, so re-apply the aspect ratio.
        self.svg_widget.renderer().setAspectRatioMode(
            Qt.AspectRatioMode.KeepAspectRatio
        )

        formula = rdMolDescriptors.CalcMolFormula(mol)
        self.status.emit(f"{formula} - {mol.GetNumAtoms()} heavy atoms")

    def _random_example(self):
        name, smiles = random.choice(list(EXAMPLES.items()))
        self.smiles_input.setText(smiles)
        self.draw()
        self.status.emit(f"{name}: {self.smiles_input.text()}")
