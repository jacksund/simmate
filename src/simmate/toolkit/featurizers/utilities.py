# -*- coding: utf-8 -*-

import numpy
from rdkit.DataStructs.cDataStructs import ExplicitBitVect


def convert_rdkit_fingerprint(
    rdkit_fp: ExplicitBitVect,
    vector_type: str,
) -> ExplicitBitVect | list | numpy.ndarray | str:
    """
    Converts an rdkit fingerprint object to some other common format. Options are:
        - rdkit (returns initial object)
        - list
        - numpy
        - base64 (for cache-based storage on disk)
    """

    if vector_type == "rdkit":
        return rdkit_fp
    elif vector_type == "list":
        return rdkit_fp.ToList()
    elif vector_type == "numpy":
        return numpy.array(rdkit_fp.ToList())
    elif vector_type == "base64":
        return numpy.array(rdkit_fp.ToBase64())
    else:
        raise Exception(f"Unknown fingerprint type: {vector_type}")


def load_rdkit_fingerprint_from_base64(
    fp_base64: str,
    nbits: int = 2048,
) -> ExplicitBitVect:
    """
    Reloads an rdkit fingerprint (ExplicitBitVect object) from a base64 string.

    This is commonly used when fingerprints are cached to disk with large datasets
    """
    fp = ExplicitBitVect(2048)
    fp.FromBase64(fp_base64)
    return fp
