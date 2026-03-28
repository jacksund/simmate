# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule as MoleculeMixin


class Molecule(MoleculeMixin):
    """
    A chemical molecule.

    This table stores the molecular structure (2D or 3D) and associated
    cheminformatics features (SMILES, InChI, etc.).
    """

    class Meta:
        db_table = "inventory_management__molecules"
