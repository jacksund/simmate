# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import ChemSpaceFreedomSpaceMolecule


class ChemSpaceFreedomSpaceMoleculeTable(DynamicTableForm):
    table = ChemSpaceFreedomSpaceMolecule
    html_display_name = "ChemSpace Freedom"
    html_description_short = (
        "A vast catalog of commercially available chemical building blocks and "
        "lead-like compounds from ChemSpace. This dataset focuses on the "
        "'Freedom Space'—a collection of billions of accessible molecules for "
        "rapid procurement."
    )
