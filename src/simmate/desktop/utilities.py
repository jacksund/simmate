"""
Shared helpers for the desktop app: molecule rendering and plot toolbars.
"""

import pyqtgraph as pg
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget
from rdkit import Chem
from rdkit.Chem import AllChem, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


def mol_to_svg(
    mol: Chem.Mol, width=600, height=450, highlight_atoms=(), highlight_bonds=()
) -> bytes:
    """Render a 2D depiction of `mol` as SVG bytes (ready for QSvgWidget.load)."""
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    drawer.drawOptions().addStereoAnnotation = True
    drawer.drawOptions().clearBackground = (
        False  # transparent; let the widget show through
    )
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer,
        mol,
        highlightAtoms=list(highlight_atoms),
        highlightBonds=list(highlight_bonds),
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText().encode()


def mol_to_png(
    mol: Chem.Mol, width=180, height=120, highlight_atoms=(), highlight_bonds=()
) -> bytes:
    """Render a small raster depiction; cheaper than SVG for many table thumbnails."""
    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    drawer.drawOptions().clearBackground = (
        False  # transparent so row highlights show through
    )
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer,
        mol,
        highlightAtoms=list(highlight_atoms),
        highlightBonds=list(highlight_bonds),
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def align_to_query(
    mol: Chem.Mol, query: Chem.Mol | None
) -> tuple[Chem.Mol, tuple, tuple]:
    """Match `query` in `mol` and lay `mol` out so the match sits like the query's 2D coords.

    Returns (mol to draw, matched atom indices, matched bond indices). Without a query
    or a match, `mol` comes back untouched with nothing highlighted.
    """
    match = mol.GetSubstructMatch(query) if query is not None else ()
    if not match:
        return mol, (), ()
    bonds = tuple(
        mol.GetBondBetweenAtoms(
            match[bond.GetBeginAtomIdx()], match[bond.GetEndAtomIdx()]
        ).GetIdx()
        for bond in query.GetBonds()
    )
    aligned = Chem.Mol(mol)
    if query.GetNumConformers():
        rdDepictor.GenerateDepictionMatching2DStructure(
            aligned, query, atomMap=list(enumerate(match))
        )
    return aligned, match, bonds


def embed_3d(mol: Chem.Mol) -> Chem.Mol | None:
    """Generate a 3D conformer (hydrogens added, MMFF-optimized), or None if embedding fails."""
    mol_3d = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol_3d, randomSeed=0xF00D) != 0:
        return None
    AllChem.MMFFOptimizeMolecule(mol_3d)
    return mol_3d


class PlotToolbar(QWidget):
    """Plotly-style controls for a PlotWidget.

    - Zoom mode (default): left-drag draws a box and zooms to it.
    - Pan mode: left-drag moves the view.
    - Scroll zooms and middle-drag pans in either mode.
    - "Reset view" or double-clicking the plot fits all the data again.
    """

    def __init__(self, plot: pg.PlotWidget):
        super().__init__()
        self.view_box = plot.getPlotItem().getViewBox()
        plot.hideButtons()  # pyqtgraph's tiny "A" autorange button; Reset view replaces it
        plot.scene().sigMouseClicked.connect(self._on_click)

        zoom_button = QPushButton("Zoom")
        pan_button = QPushButton("Pan")
        mode_group = QButtonGroup(
            self
        )  # makes the two checkable buttons mutually exclusive
        for button, mode in [
            (zoom_button, pg.ViewBox.RectMode),
            (pan_button, pg.ViewBox.PanMode),
        ]:
            button.setCheckable(True)
            button.toggled.connect(
                lambda on, m=mode: on and self.view_box.setMouseMode(m)
            )
            mode_group.addButton(button)
        zoom_button.setChecked(True)

        reset_button = QPushButton("Reset view")
        reset_button.clicked.connect(self.reset_view)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(zoom_button)
        layout.addWidget(pan_button)
        layout.addWidget(reset_button)

    def reset_view(self):
        self.view_box.autoRange()

    def _on_click(self, event):
        if event.double():
            self.reset_view()
