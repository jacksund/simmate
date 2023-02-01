# -*- coding: utf-8 -*-

from simmate.toolkit.validators.fingerprint.base import FingerprintValidator

from .featurizers import CrystalNNFingerprint as cnnf
from .featurizers import SiteStatsFingerprint as ssf


class CrystalNNFingerprint(FingerprintValidator):
    @staticmethod
    def get_featurizer(
        stat_options: list[str] = ["mean", "std_dev", "minimum", "maximum"],
        **crystalnn_options,
    ):
        # make the matminer featurizer object
        # if it isnt set, we will use the default, which is set to what the Materials project uses
        if crystalnn_options:
            sitefingerprint_method = cnnf(**crystalnn_options)
        else:
            # see https://materialsproject.org/docs/structuresimilarity
            sitefingerprint_method = cnnf.from_preset(
                "ops", distance_cutoffs=None, x_diff_weight=0
            )
        # now that we made the sitefingerprint_method, we can input it into the
        # structurefingerprint_method which finishes up the featurizer
        featurizer = ssf(sitefingerprint_method, stats=stat_options)
        return featurizer
