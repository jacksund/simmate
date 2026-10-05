import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QVBoxLayout, QWidget

from simmate.toolkit import Molecule

# CPK-style colors (RGBA, 0-1); anything not listed is drawn pink.
ELEMENT_COLORS = {
    "H": (0.9, 0.9, 0.9, 1),
    "C": (0.35, 0.35, 0.35, 1),
    "N": (0.2, 0.3, 0.95, 1),
    "O": (0.95, 0.15, 0.1, 1),
    "F": (0.5, 0.9, 0.3, 1),
    "Cl": (0.15, 0.85, 0.15, 1),
    "Br": (0.6, 0.15, 0.1, 1),
    "I": (0.4, 0.0, 0.7, 1),
    "S": (0.95, 0.85, 0.2, 1),
    "P": (1.0, 0.5, 0.0, 1),
}
DEFAULT_COLOR = (1.0, 0.4, 0.7, 1)
BOND_COLOR = (0.7, 0.7, 0.7, 1)
ATOM_RADIUS = 0.35
HYDROGEN_RADIUS = 0.22
BOND_RADIUS = 0.1


class Molecule3DView(QWidget):
    """A simple ball-and-stick view of a molecule's 3D conformer.

    Left-drag to orbit, right/middle-drag to pan, scroll to zoom.
    """

    def __init__(self):
        super().__init__()
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor("w")
        self.view.setMinimumSize(240, 180)
        self.items: list[gl.GLMeshItem] = []
        self.molecule: Molecule | None = None  # the one drawn now

        # Built once and reused by every atom/bond item.
        self.sphere = gl.MeshData.sphere(rows=12, cols=16, radius=1.0)
        self.cylinder = gl.MeshData.cylinder(
            rows=1, cols=12, radius=[BOND_RADIUS, BOND_RADIUS], length=1.0
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

    def show_mol(self, molecule: Molecule | None):
        """Draw `molecule` (which must be 3D), or clear the view for None."""
        if molecule is self.molecule:
            return  # already drawn; rebuilding every mesh is costly
        self.molecule = molecule
        for item in self.items:
            self.view.removeItem(item)
        self.items.clear()
        if molecule is None:
            return

        atoms = molecule.atom_list
        positions = np.array([atom["coords"] for atom in atoms])
        positions = positions - positions.mean(axis=0)

        for atom, position in zip(atoms, positions):
            symbol = atom["element"]
            radius = HYDROGEN_RADIUS if symbol == "H" else ATOM_RADIUS
            item = self._add(self.sphere, ELEMENT_COLORS.get(symbol, DEFAULT_COLOR))
            item.scale(radius, radius, radius)
            item.translate(*position)

        for bond in molecule.bond_list:
            start = positions[bond["begin"]]
            vector = positions[bond["end"]] - start
            length = np.linalg.norm(vector)
            item = self._add(self.cylinder, BOND_COLOR)
            # The cylinder runs along +z from the origin; stretch it to the bond's
            # length, turn it to point along the bond, then move it to the start atom.
            item.scale(1, 1, length)
            axis = np.cross((0, 0, 1), vector)
            angle = np.degrees(np.arccos(np.clip(vector[2] / length, -1, 1)))
            if np.linalg.norm(axis) > 1e-6:
                item.rotate(angle, *axis)
            elif vector[2] < 0:
                item.rotate(180, 1, 0, 0)
            item.translate(*start)

        size = np.ptp(positions, axis=0).max() if len(positions) > 1 else 1
        self.view.setCameraPosition(distance=size + 3)

    def _add(self, meshdata: gl.MeshData, color: tuple) -> gl.GLMeshItem:
        item = gl.GLMeshItem(
            meshdata=meshdata, smooth=True, color=color, shader="shaded"
        )
        self.view.addItem(item)
        self.items.append(item)
        return item
