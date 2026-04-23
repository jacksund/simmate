# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import EmoleculesMolecule, EmoleculesSupplierOffer


class EmoleculesSupplierOfferComponent(TableComponent):
    table = EmoleculesSupplierOffer
    display_name = "eMolecules Building Blocks Offers"
    description_short = "A vendor catalog of chemical 'building-blocks'"
