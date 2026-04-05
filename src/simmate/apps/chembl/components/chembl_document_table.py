# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import ChemblDocument


class ChemblDocumentTable(DynamicTableForm):
    """
    A dynamic table and search form for ChEMBL documents.
    """

    table = ChemblDocument
