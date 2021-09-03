##############################################################################

# List of MatMiner featurizers and (TO-DO) whether they're good for fingerprinting
# from matminer.featurizers.structure import
#
# DensityFeatures
# Dimensionality
# ElectronicRadialDistributionFunction
# GlobalSymmetryFeatures
# RadialDistributionFunction
# PartialRadialDistributionFunction
# CoulombMatrix
# SineCoulombMatrix
# OrbitalFieldMatrix
# MinimumRelativeDistances
# EwaldEnergy
# BondFractions
# BagofBonds
# StructuralHeterogeneity
# MaximumPackingEfficiency
# ChemicalOrdering
# StructureComposition
# XRDPowderPattern
# CGCNNFeaturizer
# JarvisCFID
# SOAP
# GlobalInstabilityIndex
# StructuralComplexity
# SiteStatsFingerprint
#       from matminer.featurizers.site import
#       CrystalNNFingerprint
#       AGNIFingerprints
#       OPSiteFingerprint
#       VoronoiFingerprint
#       IntersticeDistribution
#       ChemicalSRO
#       GaussianSymmFunc
#       EwaldSiteEnergy
#       ChemEnvSiteFingerprint
#       CoordinationNumber
#       GeneralizedRadialDistributionFunction
#       AngularFourierSeries
#       LocalPropertyDifference
#       BondOrientationalParameter
#       SiteElementalProperty
#       AverageBondLength
#       AverageBondAngle

##############################################################################

#!!! THIS SHOULD BE MOVED TO MATMINER!! Speak with their devs on github

import numpy as np

from matminer.featurizers.base import BaseFeaturizer
from matminer.featurizers.site import (
    OPSiteFingerprint,
    CoordinationNumber,
    LocalPropertyDifference,
    AverageBondAngle,
    AverageBondLength,
    CrystalNNFingerprint,
)
from matminer.featurizers.utils.stats import PropertyStats
from pymatgen.analysis.local_env import VoronoiNN


class PartialsSiteStatsFingerprint(BaseFeaturizer):
    """
    Computes statistics of properties across all sites in a structure, and
    breaks these down by element. This featurizer first uses a site featurizer
    class (see site.py for options) to compute features of each site of a
    specific element in a structure, and then computes features of the entire
    structure by measuring statistics of each attribute.
    Features:
        - Returns each statistic of each site feature, broken down by element
    """

    def __init__(
        self,
        site_featurizer,
        stats=("mean", "std_dev"),
        elements=None,
        covariance=False,
    ):
        """
        Args:
            site_featurizer (BaseFeaturizer): a site-based featurizer
            stats ([str]): list of weighted statistics to compute for each feature.
                If stats is None, a list is returned for each features
                that contains the calculated feature for each site in the
                structure.
                *Note for nth mode, stat must be 'n*_mode'; e.g. stat='2nd_mode'
            elements ([str]): list of elements to include. Default is all.
            covariance (bool): Whether to compute the covariance of site features
        """

        self.site_featurizer = site_featurizer
        self.stats = tuple([stats]) if type(stats) == str else stats
        if self.stats and "_mode" in "".join(self.stats):
            nmodes = 0
            for stat in self.stats:
                if "_mode" in stat and int(stat[0]) > nmodes:
                    nmodes = int(stat[0])
            self.nmodes = nmodes

        self.elements_ = elements
        self.covariance = covariance

    def fit(self, X, y=None):
        """Define the list of elements to be included in the PRDF. By default,
        the PRDF will include all of the elements in `X`
        Args:
            X: (numpy array nx1) structures used in the training set. Each entry
                must be Pymatgen Structure objects.
            y: *Not used*
            fit_kwargs: *not used*
        Returns:
            self
        """

        elements = []
        for s in X:
            s_elements = [e.symbol for e in s.composition.elements]
            for e in s_elements:
                if e not in elements:
                    elements.append(e)

        # Store the elements
        self.elements_ = elements

        return self

    @property
    def _site_labels(self):
        return self.site_featurizer.feature_labels()

    def featurize(self, s):
        """
        Get PSSF of the input structure.
        Args:
            s: Pymatgen Structure object.
        Returns:
            pssf: 1D array of each element's ssf
        """

        if self.elements_ is None:
            raise Exception("You must run 'fit' first!")

        output = []
        for e in self.elements_:
            pssf_stats = self.compute_pssf(
                s, e
            )  # Assemble the PSSF for the given element
            output.append(pssf_stats)

        return np.hstack(output)

    def compute_pssf(
        self, s, e
    ):  #!! THIS IS FOR A SET ANALYSIS - CHANGE TO SINGLE ELEMENT
        # Get each feature for each site
        vals = [[] for t in self._site_labels]
        for i, site in enumerate(s.sites):
            if site.specie.symbol == e:
                opvalstmp = self.site_featurizer.featurize(s, i)
                for j, opval in enumerate(opvalstmp):
                    if opval is None:
                        vals[j].append(0.0)
                    else:
                        vals[j].append(opval)

        # If the user does not request statistics, return the site features now
        if self.stats is None:
            return vals

        # Compute the requested statistics
        stats = []
        for op in vals:
            for stat in self.stats:
                stats.append(PropertyStats().calc_stat(op, stat))

        # If desired, compute covariances
        if self.covariance:
            if len(s) == 1:
                stats.extend([0] * int(len(vals) * (len(vals) - 1) / 2))
            else:
                covar = np.cov(vals)
                tri_ind = np.triu_indices(len(vals), 1)
                stats.extend(covar[tri_ind].tolist())

        return stats

    def feature_labels(self):  #!!!! CHANGE THIS TO ACCOUNT FOR MULTIPLE ELEMENTS
        if self.stats:
            labels = []
            # Make labels associated with the statistics
            for attr in self._site_labels:
                for stat in self.stats:
                    labels.append("%s %s" % (stat, attr))

            # Make labels associated with the site labels
            if self.covariance:
                sl = self._site_labels
                for i, sa in enumerate(sl):
                    for sb in sl[(i + 1) :]:
                        labels.append("covariance %s-%s" % (sa, sb))
            return labels
        else:
            return self._site_labels

    def citations(self):
        return self.site_featurizer.citations()

    def implementors(self):
        return ["Jack D. Sundberg"]

    @staticmethod
    def from_preset(preset, **kwargs):
        """
        Create a PartialsSiteStatsFingerprint class according to a preset
        Args:
            preset (str) - Name of preset
            kwargs - Options for PartialsSiteStatsFingerprint
        """

        if preset == "CrystalNNFingerprint_cn":
            return PartialsSiteStatsFingerprint(
                CrystalNNFingerprint.from_preset("cn", cation_anion=False), **kwargs
            )

        elif preset == "CrystalNNFingerprint_cn_cation_anion":
            return PartialsSiteStatsFingerprint(
                CrystalNNFingerprint.from_preset("cn", cation_anion=True), **kwargs
            )

        elif preset == "CrystalNNFingerprint_ops":
            return PartialsSiteStatsFingerprint(
                CrystalNNFingerprint.from_preset("ops", cation_anion=False), **kwargs
            )

        elif preset == "CrystalNNFingerprint_ops_cation_anion":
            return PartialsSiteStatsFingerprint(
                CrystalNNFingerprint.from_preset("ops", cation_anion=True), **kwargs
            )

        elif preset == "OPSiteFingerprint":
            return PartialsSiteStatsFingerprint(OPSiteFingerprint(), **kwargs)

        elif preset == "LocalPropertyDifference_ward-prb-2017":
            return PartialsSiteStatsFingerprint(
                LocalPropertyDifference.from_preset("ward-prb-2017"),
                stats=["minimum", "maximum", "range", "mean", "avg_dev"],
            )

        elif preset == "CoordinationNumber_ward-prb-2017":
            return PartialsSiteStatsFingerprint(
                CoordinationNumber(
                    nn=VoronoiNN(weight="area"), use_weights="effective"
                ),
                stats=["minimum", "maximum", "range", "mean", "avg_dev"],
            )

        elif preset == "Composition-dejong2016_AD":
            return PartialsSiteStatsFingerprint(
                LocalPropertyDifference(
                    properties=[
                        "Number",
                        "AtomicWeight",
                        "Column",
                        "Row",
                        "CovalentRadius",
                        "Electronegativity",
                    ],
                    signed=False,
                ),
                stats=["holder_mean::%d" % d for d in range(0, 4 + 1)] + ["std_dev"],
            )

        elif preset == "Composition-dejong2016_SD":
            return PartialsSiteStatsFingerprint(
                LocalPropertyDifference(
                    properties=[
                        "Number",
                        "AtomicWeight",
                        "Column",
                        "Row",
                        "CovalentRadius",
                        "Electronegativity",
                    ],
                    signed=True,
                ),
                stats=["holder_mean::%d" % d for d in [1, 2, 4]] + ["std_dev"],
            )

        elif preset == "BondLength-dejong2016":
            return PartialsSiteStatsFingerprint(
                AverageBondLength(VoronoiNN()),
                stats=["holder_mean::%d" % d for d in range(-4, 4 + 1)]
                + ["std_dev", "geom_std_dev"],
            )

        elif preset == "BondAngle-dejong2016":
            return PartialsSiteStatsFingerprint(
                AverageBondAngle(VoronoiNN()),
                stats=["holder_mean::%d" % d for d in range(-4, 4 + 1)]
                + ["std_dev", "geom_std_dev"],
            )

        else:
            # TODO: Why assume coordination number? Should this just raise an error? - lw
            # One of the various Coordination Number presets:
            # MinimumVIRENN, MinimumDistanceNN, JmolNN, VoronoiNN, etc.
            try:
                return PartialsSiteStatsFingerprint(
                    CoordinationNumber.from_preset(preset), **kwargs
                )
            except:
                pass

        raise ValueError("Unrecognized preset!")
