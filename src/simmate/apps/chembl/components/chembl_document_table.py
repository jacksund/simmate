# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import ChemblDocument


class ChemblDocumentTable(DynamicTableForm):
    """
    A dynamic table and search form for ChEMBL documents.
    """

    table = ChemblDocument
