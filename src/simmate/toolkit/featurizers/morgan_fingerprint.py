# -*- coding: utf-8 -*-

from rdkit.Chem import AllChem

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer

from .utils import convert_rdkit_fingerprint


class MorganFingerprint(Featurizer):
    """
    Uses RDKit to generate Morgan Fingerprints (count fingerprint, aka circular fingerprint).

    Recommended similarity scoring: Dice
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        vector_type: str = "numpy",
        radius: int = 2,
        size: int = 1024,
        **kwargs,
    ):
        fpgen = AllChem.GetMorganGenerator(radius=radius, fpSize=size, **kwargs)
        rdkit_fp = fpgen.GetCountFingerprint(molecule.rdkit_molecule)
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
