# -*- coding: utf-8 -*-

import numpy
from rdkit.Chem import AllChem


def convert_rdkit_fingerprint(
    rdkit_fp: AllChem.DataStructs.cDataStructs.ExplicitBitVect,
    vector_type: str,
) -> any:
    """
    Converts an rdkit fingerprint object to some other common format. Options are:
        - rdkit (returns initial object)
        - list
        - numpy
        - base64
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
