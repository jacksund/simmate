# -*- coding: utf-8 -*-

import numpy

from .base import SimilarityEngine


class Identity(SimilarityEngine):
    """
    The identity comparison gives 1 when `fp1 == fp2` for ALL values and 0 otherwise.
    """

    @classmethod
    def get_similarity(
        cls,
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
        # backend: str = "numpy",
    ) -> float:
        return 1 if (fingerprint1 == fingerprint2).all() else 0
