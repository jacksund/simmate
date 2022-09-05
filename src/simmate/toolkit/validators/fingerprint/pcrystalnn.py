# -*- coding: utf-8 -*-

import logging

import numpy

from simmate.toolkit import Composition
from simmate.toolkit.validators.fingerprint.base import FingerprintValidator

from .featurizers import CrystalNNFingerprint as cnnf
from .featurizers import SiteStatsFingerprint as pssf  # PartialsSiteStatsFingerprint


class PartialCrystalNNFingerprint(FingerprintValidator):
    @staticmethod
    def get_featurizer(
        composition: Composition,
        stat_options: list[str] = ["mean", "std_dev", "minimum", "maximum"],
        **crystalnn_options,
    ):

        # BUG: waiting on this pSS to be added to matminer. See the following PR:
        #   https://github.com/hackingmaterials/matminer/pull/809
        logging.warning(
            "PartialsSiteStatsFingerprint current acts as a SiteStatsFingerprint. "
            "We are waiting on a new MatMiner release to fix this issue."
        )

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
