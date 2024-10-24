# -*- coding: utf-8 -*-

from simmate.toolkit.smarts_sets.base import SmartsSet


class CdkFunctionalGroups(SmartsSet):
    """
    An extended list of 306** functional group checks from CDK's
    `SubstructureFingerprinter` class.

    The full set can be accessed at...
        https://cdk.github.io/cdk/2.2/docs/api/org/openscience/cdk/fingerprint/SubstructureFingerprinter.html

    ** NOTE: RDKit was unable to load 3 of the orginal smarts queries, so these
    3 were removed from the set (making the final set 303 fxnal groups). These
    queries were:
        - Cis double bond,*&#47[D2]=[D2]/*
        - Trans double bond,*&#47[D2]=[D2]/*
        - Salt,"([-1,-2,-3,-4,-5,-6,-7]).([+1,+2,+3,+4,+5,+6,+7])"

    (consider opening an issue with RDKit for these 3 queries)
    """

    source_file = "cdk_fxn_groups.csv"
