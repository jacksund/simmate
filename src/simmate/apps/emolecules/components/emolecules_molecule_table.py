# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm
from simmate.website.htmx.components import MoleculeInput

from ..models import EmoleculesMolecule, EmoleculesSupplierOffer


class EmoleculesMoleculeTable(DynamicTableForm, MoleculeInput):
    table = EmoleculesMolecule
    display_name = "eMolecules"
    description_short = (
        "A comprehensive, vendor-neutral catalog of chemicals from eMolecules. "
        "It aggregates data from hundreds of suppliers to provide up-to-date "
        "availability, pricing, and chemical information for procurement and "
        "research."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "search": "core/base_data_types/molecule_form.html",
    }

    enabled_forms = ["search"]
