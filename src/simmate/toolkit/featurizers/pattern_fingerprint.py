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
        vector_type: str = "numpy",
        explicit_h: bool = False,
        **kwargs,
    ) -> numpy.array:
        # some substructure queries require explicit H, and the pattern
        # fingerprint changes when H is present
        if explicit_h:
            molecule.add_hydrogens()
        rdkit_fp = AllChem.PatternFingerprint(molecule.rdkit_molecule, **kwargs)
        return convert_rdkit_fingerprint(rdkit_fp, vector_type)
