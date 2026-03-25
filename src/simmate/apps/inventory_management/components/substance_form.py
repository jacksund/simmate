# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import Substance


class SubstanceForm(DynamicTableForm):
    table = Substance

    display_name = "Chemical Substances"
    description_short = (
        "A substance is a specific element or compound with uniform composition+structure. "
        "As a general rule of thumb, if there is a CAS number (from ACS) or "
        "CID (from PubChem) assigned to it, then it is likely a chemical substance. "
        "In addition, this table includes both specified and unspecified "
        "stereochemical compounds, where flat structures and those with "
        "'and'/'or' notations are separate entries. Allotropes are also "
        "separate entries."
    )
