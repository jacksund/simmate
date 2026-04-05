# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import ChemblAssayResult


class ChemblAssayResultTable(DynamicTableForm):
    """
    A dynamic table and search form for ChEMBL assay results.
    """

    table = ChemblAssayResult
