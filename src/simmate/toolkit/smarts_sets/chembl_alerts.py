# -*- coding: utf-8 -*-

from simmate.toolkit.smarts_sets.base import SmartsSet


class ChemblAlerts(SmartsSet):
    """
    The set of 'structural alerts' pulled from the ChEMBL database.

    This includes subsets from Glaxo, Dundee, BMS, & PAINS alerts.
    """

    source_file = "chembl_alerts_v33.csv"
