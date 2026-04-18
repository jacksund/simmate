# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent
from simmate.website.htmx.components import MoleculeInput

from ..models import EmoleculesMolecule, EmoleculesSupplierOffer


class EmoleculesMoleculeComponent(TableComponent, MoleculeInput):
    table = EmoleculesMolecule
    display_name = "eMolecules"
    description_short = (
        "A comprehensive, vendor-neutral catalog of chemicals from eMolecules. "
        "It aggregates data from hundreds of suppliers to provide up-to-date "
        "availability, pricing, and chemical information for procurement and "
        "research."
    )
    template_names = {
        "search": "core/base_data_types/molecule_form.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry", "search"]
