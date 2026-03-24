# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import EmoleculesMolecule, EmoleculesSupplierOffer


class EmoleculesSupplierOfferTable(DynamicTableForm):
    table = EmoleculesSupplierOffer
    display_name = "eMolecules Building Blocks Offers"
    description_short = "A vendor catalog of chemical 'building-blocks'"
