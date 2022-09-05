# -*- coding: utf-8 -*-

import warnings

# BUG: Importing matminer featurizers print a tqdm error so we silence them
# by importing them all together here.
with warnings.catch_warnings(record=True):
    from matminer.featurizers.site import CrystalNNFingerprint
    from matminer.featurizers.structure import (
        PartialRadialDistributionFunction,
        RadialDistributionFunction,
        SiteStatsFingerprint,
    )
