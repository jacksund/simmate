# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit.similarity.base import SimilarityEngine


class Cosine(SimilarityEngine):
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

    # A useful thread for other implementations of cosine distance to benchmark
    #   https://stackoverflow.com/questions/18424228

    @staticmethod
    def _sklearn_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        from sklearn.metrics.pairwise import cosine_similarity

        return cosine_similarity([fingerprint1], [fingerprint2])

    @staticmethod
    def _scipy_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        from scipy.spatial import distance

        return distance.cosine(fingerprint1, fingerprint2)

    @staticmethod
    def _numpy_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        return numpy.dot(fingerprint1, fingerprint2) / (
            numpy.linalg.norm(fingerprint1) * numpy.linalg.norm(fingerprint2)
        )
