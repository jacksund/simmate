# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit.similarity.base import SimilarityEngine


class Euclidean(SimilarityEngine):
    @classmethod
    def get_similarity(
        cls,
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
        # backend: str = "numpy",
    ) -> float:
        raise NotImplementedError("This method is still being written")

    # -------------------------------------------------------------------------

    # ALTERNATIVE METHODS FOR CALCULATING

    @staticmethod
    def _scipy_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        from scipy.spatial import distance

        return distance.euclidean(fingerprint1, fingerprint2)

    @staticmethod
    def _numpy_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        return numpy.linalg.norm(fingerprint1 - fingerprint2)
