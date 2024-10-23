# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer


class PropertyGrabber(Featurizer):
    """
    Grabs attributes from the molecule object
    """

    @staticmethod
    def featurize(
        molecule: Molecule,
        properties: list[str],  # e.g. ["num_rings", "molecular_weight", ...]
        **kwargs,
    ) -> numpy.array:
        values = [getattr(molecule, p) for p in properties]
        return numpy.array(values)
