# -*- coding: utf-8 -*-

import numpy


class SimilarityEngine:
    """
    A base class for measuring similarities of fingerprints
    """

    # 1 of the 4 methods must be overwritten:
    #   1. get_similarity
    #   2. get_distance
    #   3. get_similarity_series
    #   4. get_distance_series
    # If you choose 2 or 4, make sure you set is_distance_based to True.
    # New method can be either a classmethod or staticmethod.

    is_distance_based: bool = False

    # -------------------------------------------------------------------------

    @classmethod
    def convert_to_similarity(self, distance: float) -> float:
        return 1 - distance

    @classmethod
    def convert_to_distance(self, similarity: float) -> float:
        return 1 - similarity

    # -------------------------------------------------------------------------

    @classmethod
    def get_similarity(
        cls,
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ) -> float:
        """
        Compute the similarity between two fingerprints using the specified
        similarity method.
        """
        return cls.get_similarity_series(fingerprint1, [fingerprint2])[0]

    @classmethod
    def get_similarity_series(
        cls,
        fingerprint1: any,
        fingerprints: list[any],
        **kwargs,
    ) -> list:
        return [
            cls.get_similarity(fingerprint1, fingerprint2)
            for fingerprint2 in fingerprints
        ]

    def get_similarity_matrix(self, fingerprints: list) -> list[list]:
        """
        Calculates the pairwise similarity scores between all molecules.
        Note that the similarity matrix is symmetric, so only the upper
        triangle of the matrix needs to be calculated. The full symmetric
        matrix is still returned though
        """
        num_molecules = len(self.molecules)
        similarity_matrix = numpy.zeros((num_molecules, num_molecules))
        for i in range(num_molecules):
            for j in range(i + 1, num_molecules):
                similarity = self.similarity_func(
                    self.fingerprints[i],
                    self.fingerprints[j],
                )
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity
        return similarity_matrix

    # -------------------------------------------------------------------------

    # Methods for converting from similarity to distance (aka dissimilarity)

    # !!! maybe have a get_distance method that is (1-sim) or (1/sim)?
    # I may need a "is normalized" or "normalize" methods + properties

    @staticmethod
    def get_distance(
        fingerprint1: numpy.array,
        fingerprint2: numpy.array,
    ) -> float:
        raise NotImplementedError("This method is still being written")

    @classmethod
    def get_distance_series(
        cls,
        fingerprint1: any,
        fingerprints: list[any],
        **kwargs,
    ) -> list:
        similarities = cls.get_similarity_series(
            fingerprint1,
            fingerprints,
            **kwargs,
        )
        return [cls.convert_to_distance(sim) for sim in similarities]

    # -------------------------------------------------------------------------
