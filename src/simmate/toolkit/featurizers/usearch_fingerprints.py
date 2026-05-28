# -*- coding: utf-8 -*-

from .ecfp4_fingerprint import Ecfp4Fingerprint
from .fcfp4_fingerprint import Fcfp4Fingerprint
from .maccs_fingerprint import MaccsFingerprint
from .multi_featurizer import MultiFeaturizer


class USearchFingerprints(MultiFeaturizer):
    """
    Returns a 3-tuple of packed-bit fingerprints (MACCS, ECFP4, FCFP4) per
    molecule, matching the format expected by USearch binary indexes.

    Output shapes: MACCS → (21,), ECFP4 → (256,), FCFP4 → (256,) bytes.
    """

    featurizers = [
        (MaccsFingerprint, {"vector_type": "numpy_packbits"}),
        (Ecfp4Fingerprint, {"vector_type": "numpy_packbits"}),
        (Fcfp4Fingerprint, {"vector_type": "numpy_packbits"}),
    ]
