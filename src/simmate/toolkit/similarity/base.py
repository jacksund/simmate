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

    matrix_mode: bool = "pairwise"

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
        return cls.get_similarity_series(fingerprint1, numpy.array([fingerprint2]))[0]

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

    @classmethod
    def get_similarity_matrix(cls, fingerprints: list) -> list[list]:
        """
        Calculates the pairwise similarity scores between all molecules.
        Note that the similarity matrix is symmetric, so only the upper
        triangle of the matrix needs to be calculated. The full symmetric
        matrix is still returned.

        Note, if individual calls to `get_similarity` are slow due to overhead
        of calling another layer (e.g. numba), switch to `matrix_mode="series"`
        where `get_similarity_series` will be used instead.
        """
        if cls.matrix_mode == "pairwise":
            num_fingerprints = len(fingerprints)
            similarity_matrix = numpy.zeros((num_fingerprints, num_fingerprints))
            for i in range(num_fingerprints):
                for j in range(i + 1, num_fingerprints):
                    similarity = cls.get_similarity(
                        fingerprints[i],
                        fingerprints[j],
                    )
                    similarity_matrix[i][j] = similarity
                    similarity_matrix[j][i] = similarity
            return similarity_matrix

        elif cls.matrix_mode == "series":
            # TODO: update this alg to only calculate half the matrix then mirror it
            fingerprints = numpy.array(fingerprints)
            return numpy.array(
                [
                    cls.get_similarity_series(fingerprint, fingerprints)
                    for fingerprint in fingerprints
                ]
            )

    @classmethod
    def get_similarity_mean(cls, fingerprints: list) -> float:
        # we want the matrix mean NOT including the diagonal
        # https://stackoverflow.com/questions/62250799
        # (total_sum - diagonal_sum) / (num_elements - num_diagonal_elements)
        matrix = cls.get_similarity_matrix(fingerprints)
        return (matrix.sum() - matrix.diagonal().sum()) / (
            len(matrix) ** 2 - len(matrix.diagonal())
        )

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
