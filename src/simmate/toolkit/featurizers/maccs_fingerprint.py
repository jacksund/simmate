# -*- coding: utf-8 -*-

from rdkit.Chem import MACCSkeys

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer

from .utils import convert_rdkit_fingerprint


class MaccsFingerprint(Featurizer):
    """
    Uses RDKit to generate MACCS Keys (166-bit structural fingerprint).

    Recommended similarity scoring: Tanimoto
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        vector_type: str = "numpy",
        **kwargs,
    ):
        rdkit_fp = MACCSkeys.GenMACCSKeys(molecule.rdkit_molecule)
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
