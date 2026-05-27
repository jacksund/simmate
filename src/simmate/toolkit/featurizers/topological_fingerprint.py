# -*- coding: utf-8 -*-

from rdkit.Chem import AllChem

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer

from .utils import convert_rdkit_fingerprint


class TopologicalFingerprint(Featurizer):
    """
    Uses RDKit to generate Topological (RDKit) Fingerprints.

    Recommended similarity scoring: Tanimoto
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        vector_type: str = "numpy",
        **kwargs,
    ):
        fpgen = AllChem.GetRDKitFPGenerator(**kwargs)
        rdkit_fp = fpgen.GetFingerprint(molecule.rdkit_molecule)
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
