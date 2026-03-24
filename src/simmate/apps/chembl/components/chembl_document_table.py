# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import ChemblAssayResult, ChemblDocument, ChemblMolecule


class ChemblDocumentTable(DynamicTableForm):
    table = ChemblDocument
