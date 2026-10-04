"""
Shared helpers for the desktop app: molecule rendering and plot toolbars.
"""

import pyqtgraph as pg
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D


def mol_to_svg(mol: Chem.Mol, width=600, height=450, highlight_atoms=()) -> bytes:
    """Render a 2D depiction of `mol` as SVG bytes (ready for QSvgWidget.load)."""
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    drawer.drawOptions().addStereoAnnotation = True
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer, mol, highlightAtoms=list(highlight_atoms)
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText().encode()


def mol_to_png(mol: Chem.Mol, width=180, height=120, highlight_atoms=()) -> bytes:
    """Render a small raster depiction; cheaper than SVG for many table thumbnails."""
    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer, mol, highlightAtoms=list(highlight_atoms)
    )
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


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
