# -*- coding: utf-8 -*-

from simmate.toolkit.validators import FingerprintValidator

from .featurizers import RadialDistributionFunction as rdf


class RdfFingerprint(FingerprintValidator):
    
    comparison_mode = "cos"

    @staticmethod
    def get_featurizer(
        cutoff=20.0,
        bin_size=0.1,
        **kwargs,
    ):
        featurizer = rdf(cutoff, bin_size, **kwargs)
        return featurizer

    
    @staticmethod
    def format_fingerprint(fingerprint):
        # the [0]['distribution'] reformats the output to an actual
        # fingerprint (1D numpy array) that we want
        return fingerprint[0]["distribution"]
