import numpy

from simmate.toolkit.similarity.base import SimilarityEngine


class Euclidean(SimilarityEngine):
    is_distance_based: bool = True

    @classmethod
    def get_distance(
        cls,
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ) -> float:
        return numpy.linalg.norm(fingerprint1 - fingerprint2)

    # -------------------------------------------------------------------------

    # ALTERNATIVE METHODS FOR CALCULATING

    @staticmethod
    def _scipy_method(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ):
        from scipy.spatial import distance

        return distance.euclidean(fingerprint1, fingerprint2)
