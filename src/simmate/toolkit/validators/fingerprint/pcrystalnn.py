# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Composition
from simmate.toolkit.validators.fingerprint.base import FingerprintValidator

from .featurizers import CrystalNNFingerprint as cnnf
from .featurizers import PartialsSiteStatsFingerprint as pssf


class PartialCrystalNNFingerprint(FingerprintValidator):
    # Defaults grab from those suggested by the Materials Project
    comparison_mode = "linalg_norm"
    distance_tolerance = 0.9
    # https://docs.materialsproject.org/methodology/materials-methodology/
    # related-materials#structure-distance-dissimilarity

    @staticmethod
    def get_featurizer(
        composition: Composition,
        stat_options: list[str] = ["mean", "std_dev"],  # , "minimum", "maximum"
        **crystalnn_options,
    ):
        # Note, defaults give the equivalent fingerprint method:
        # PartialsSiteStatsFingerprint.from_preset("CrystalNNFingerprint_ops")

        # make the matminer featurizer object using the provided settings
        if crystalnn_options:
            sitefingerprint_method = cnnf(**crystalnn_options)
        # if no settings were given, we will use those from the Materials Project
        #   https://docs.materialsproject.org/user-guide/structure-similarity/
        else:
            # We change x_diff_weight to 3 here because we want the coordation
            # to be atom-dependent (best we can do is oxidation-state dependent here)
            sitefingerprint_method = cnnf.from_preset(
                "ops", distance_cutoffs=None, x_diff_weight=3
            )

        # now that we made the sitefingerprint_method, we can input it into the
        # structurefingerprint_method which finishes up the featurizer
        featurizer = pssf(sitefingerprint_method, stats=stat_options)

        # for this specific featurizer, you're supposed to use the .fit() function
        # with an example structure but really, all that does is get a list of
        # unique elements - so we can make that with a composition object
        featurizer.elements_ = numpy.array(
            [element.symbol for element in composition.elements]
        )

        return featurizer
