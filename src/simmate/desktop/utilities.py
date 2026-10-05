"""
Shared helpers for the desktop app: molecule rendering and 3D embedding.
"""

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
