# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import ChemblAssayResult


class ChemblAssayResultComponent(TableComponent):
    """
    A dynamic table and search form for ChEMBL assay results.
    """

    table = ChemblAssayResult
