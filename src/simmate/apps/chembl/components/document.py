# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import ChemblDocument


class ChemblDocumentComponent(TableComponent):
    """
    A dynamic table and search form for ChEMBL documents.
    """

    table = ChemblDocument
