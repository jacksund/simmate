# -*- coding: utf-8 -*-

from langchain.agents import tool

from simmate.toolkit import Molecule


@tool
def get_inchi_key(smiles: str) -> int:
    """Returns the inchi key for a SMILES string."""
    return Molecule.from_smiles(smiles).to_inchi_key()


@tool
def get_add_hydrogens(smiles: str) -> int:
    """add hydrogens to a SMILES string"""
    m = Molecule.from_smiles(smiles)
    m.add_hydrogens()
    return m.to_smiles(remove_hydrogen=False)


@tool
def get_num_rings(smiles: str) -> int:
    """Returns the number of rings."""
    return Molecule.from_smiles(smiles).num_rings


@tool(return_direct=True)
def get_png_image(smiles: str) -> int:
    """Returns a PIL image object of the molecule"""
    return Molecule.from_smiles(smiles).to_png()
