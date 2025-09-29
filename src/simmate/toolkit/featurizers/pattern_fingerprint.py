# -*- coding: utf-8 -*-

import numpy
from rdkit.Chem import AllChem

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer

from .utilities import convert_rdkit_fingerprint


class PatternFingerprint(Featurizer):
    """
    Uses RDkit to generate Pattern Fingerprints (as bit vectors)
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        radius: float = 2,
        nbits: int = 1024,
        vector_type: str = "numpy",
        **kwargs,
    ) -> numpy.array:
        rdkit_fp = AllChem.PatternFingerprint(molecule.rdkit_molecule, **kwargs)
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
