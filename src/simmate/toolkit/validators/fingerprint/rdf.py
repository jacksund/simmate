# -*- coding: utf-8 -*-

from simmate.toolkit.validators.fingerprint import FingerprintValidator

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

    # @staticmethod
    # def format_fingerprint(fingerprint):
    #     Consider a sigma input that smooths the function
    #     from scipy.ndimage import gaussian_filter1d
    #     new_fp = gaussian_filter1d(fp, sigma=1)
