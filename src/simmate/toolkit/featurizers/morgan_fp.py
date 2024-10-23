# -*- coding: utf-8 -*-

import numpy
from rdkit.Chem import AllChem

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer


class MorganFingerprint(Featurizer):
    """
    Uses RDkit to generate Morgan Fingerprints (as bit vectors)
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        radius: float = 2,
        nbits: int = 1024,
        **kwargs,
    ) -> numpy.array:
        fp = AllChem.GetMorganFingerprintAsBitVect(
            molecule.rdkit_molecule,
            radius=radius,
            nBits=nbits,
            **kwargs,
        )
        return numpy.array(fp.ToList())

    # TODO: return as a non-bit-vector
    # from rdkit.Chem import rdFingerprintGenerator
    # fp_gen = rdFingerprintGenerator.GetMorganGenerator(
    #     radius=radius, fpSize=nbits, useCountSimulation=countBits
    # )
