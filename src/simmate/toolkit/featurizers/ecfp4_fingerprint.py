# -*- coding: utf-8 -*-

from rdkit.Chem import AllChem

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer

from .utils import convert_rdkit_fingerprint


class Ecfp4Fingerprint(Featurizer):
    """
    Uses RDKit to generate ECFP4 Fingerprints (Morgan, radius=2, bit vector).

    Recommended similarity scoring: Tanimoto
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        vector_type: str = "numpy",
        size: int = 2048,
        **kwargs,
    ):
        rdkit_fp = AllChem.GetMorganFingerprintAsBitVect(
            molecule.rdkit_molecule, radius=2, nBits=size, **kwargs
        )
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
