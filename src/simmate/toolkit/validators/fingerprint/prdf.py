# -*- coding: utf-8 -*-

import numpy
from scipy.ndimage import gaussian_filter1d

from simmate.toolkit import Composition
from simmate.toolkit.validators.fingerprint.base import FingerprintValidator

from .featurizers import PartialRadialDistributionFunction as prdf


class PartialRdfFingerprint(FingerprintValidator):
    comparison_mode = "cos"

    @staticmethod
    def get_featurizer(
        composition: Composition,
        cutoff: float = 20.0,
        bin_size: float = 0.1,
        **kwargs,
    ):
        featurizer = prdf(cutoff, bin_size, **kwargs)

        # for this specific featurizer, you're supposed to use the .fit()
        # function with an example structure but really, all that does is get
        # a list of unique elements - so we can make that with a composition object
        featurizer.elements_ = numpy.array(
            [element.symbol for element in composition.elements]
        )

        return featurizer

    @staticmethod
    def format_fingerprint(fingerprint):
        # smooths the function
        new_fp = gaussian_filter1d(fingerprint, sigma=1)
        return new_fp
