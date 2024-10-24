# -*- coding: utf-8 -*-

import numpy
from numba import njit, prange

from simmate.toolkit.similarity.base import SimilarityEngine


class Tanimoto(SimilarityEngine):
    @classmethod
    def get_similarity_series(
        cls,
        fingerprint1: numpy.array,
        fingerprints: numpy.array,
        **kwargs,
    ) -> list:
        return cls._numba_method_serial(fingerprint1, fingerprints)

    # -------------------------------------------------------------------------

    # ALTERNATIVE METHODS FOR CALCULATING

    @staticmethod
    @njit(cache=True, parallel=True)
    def _numba_method_serial(
        fingerprint: numpy.array,
        fingerprints: numpy.array,
    ) -> numpy.array:
        # Code is from...
        #   https://stackoverflow.com/questions/64353902/

        result = numpy.zeros(fingerprints.shape[0])
        for i in prange(0, result.shape[0]):
            den = numpy.sum(numpy.bitwise_or(fingerprint, fingerprints[i]))
            if den != 0.0:
                result[i] = (
                    numpy.sum(numpy.bitwise_and(fingerprint, fingerprints[i])) / den
                )
            else:
                result[i] = 0.0
        return result

    @staticmethod
    def _rdkit_method_serial(fingerprint, fingerprints):
        from rdkit import DataStructs

        # OPTIMIZE: this is a very slow conversion to rdkit objects...
        def to_rdkit(fingerprint):
            result = DataStructs.CreateFromBitString(
                "".join([str(x) for x in fingerprint])
            )
            return result

        fingerprint_rdkit = to_rdkit(fingerprint)
        fingerprints_rdkit = [to_rdkit(fp) for fp in fingerprints]

        return DataStructs.BulkTanimotoSimilarity(
            fingerprint_rdkit,
            fingerprints_rdkit,
        )
