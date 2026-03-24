# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import EmoleculesMolecule, EmoleculesSupplierOffer


class EmoleculesMoleculeTable(DynamicTableForm):
    table = EmoleculesMolecule
    display_name = "eMolecules"
    description_short = (
        "A comprehensive, vendor-neutral catalog of chemicals from eMolecules. "
        "It aggregates data from hundreds of suppliers to provide up-to-date "
        "availability, pricing, and chemical information for procurement and "
        "research."
    )
