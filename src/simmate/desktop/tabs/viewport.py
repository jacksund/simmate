import random

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


def _tube_mesh(surface: np.ndarray) -> gl.MeshData:
    """Triangulate a (rows, cols, 3) grid that wraps around in both directions."""
    rows, cols, _ = surface.shape
    i, j = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    a = i * cols + j
    b = i * cols + (j + 1) % cols
    c = ((i + 1) % rows) * cols + j
    d = ((i + 1) % rows) * cols + (j + 1) % cols
    faces = np.concatenate([np.stack([a, b, d], -1), np.stack([a, d, c], -1)]).reshape(
        -1, 3
    )
    return gl.MeshData(vertexes=surface.reshape(-1, 3), faces=faces)


def torus(major=2.0, minor=0.7) -> gl.MeshData:
    u, v = np.meshgrid(
        np.linspace(0, 2 * np.pi, 80, endpoint=False),
        np.linspace(0, 2 * np.pi, 40, endpoint=False),
        indexing="ij",
    )
    ring = major + minor * np.cos(v)
    return _tube_mesh(
        np.stack([ring * np.cos(u), ring * np.sin(u), minor * np.sin(v)], -1)
    )


def torus_knot(p: int, q: int, radius=0.35) -> gl.MeshData:
    t = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    r = 2 + np.cos(q * t)
    curve = np.stack([r * np.cos(p * t), r * np.sin(p * t), -np.sin(q * t)], -1)

    # Build a frame along the curve (tangent/normal/binormal) to sweep a circle along it.
    tangent = np.roll(curve, -1, 0) - np.roll(curve, 1, 0)
    tangent /= np.linalg.norm(tangent, axis=1, keepdims=True)
    normal = np.roll(tangent, -1, 0) - np.roll(tangent, 1, 0)
    normal /= np.linalg.norm(normal, axis=1, keepdims=True)
    binormal = np.cross(
        normal, tangent
    )  # this order gives the same face winding as MeshData.sphere

    theta = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    circle = (
        np.cos(theta)[None, :, None] * normal[:, None, :]
        + np.sin(theta)[None, :, None] * binormal[:, None, :]
    )
    return _tube_mesh(curve[:, None, :] + radius * circle)


def blob() -> gl.MeshData:
    """A sphere with its radius perturbed by a few random low-frequency waves."""
    mesh = gl.MeshData.sphere(rows=60, cols=60, radius=2.0)
    verts = mesh.vertexes()
    unit = verts / np.linalg.norm(verts, axis=1, keepdims=True)
    bumps = sum(
        random.uniform(0.1, 0.35)
        * np.sin(unit @ np.random.normal(size=3) * random.uniform(2, 4))
        for _ in range(4)
    )
    return gl.MeshData(vertexes=unit * (2.0 + bumps)[:, None], faces=mesh.faces())


class ViewportTab(QWidget):
    """An OpenGL 3D viewport: left-drag to orbit, right/middle-drag to pan, scroll to zoom."""

    status = Signal(str)

    def __init__(self):
        super().__init__()

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor("w")
        self.view.setCameraPosition(distance=12, elevation=25)
        grid = gl.GLGridItem()
        grid.setSize(12, 12)
        grid.setColor((0, 0, 0, 76))
        grid.translate(0, 0, -3)
        self.view.addItem(grid)
        self.mesh_item = None

        random_button = QPushButton("Random object")
        random_button.clicked.connect(self.random_object)

        controls = QHBoxLayout()
        controls.addStretch()
        controls.addWidget(random_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view, stretch=1)
        layout.addLayout(controls)

        self.random_object()

    def random_object(self):
        p, q = random.choice([(2, 3), (3, 2), (2, 5), (3, 4), (3, 5)])
        name, mesh = random.choice(
            [
                ("torus", torus()),
                (f"({p},{q}) torus knot", torus_knot(p, q)),
                ("blob", blob()),
                ("sphere", gl.MeshData.sphere(rows=40, cols=40, radius=2.0)),
            ]
        )

        if self.mesh_item is not None:
            self.view.removeItem(self.mesh_item)
        color = QColor.fromHsvF(random.random(), 0.65, 0.95).getRgbF()
        self.mesh_item = gl.GLMeshItem(
            meshdata=mesh, smooth=True, color=color, shader="shaded"
        )
        self.view.addItem(self.mesh_item)
        self.status.emit(f"{name} - {len(mesh.faces())} triangles")
