# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import ChemSpaceFreedomSpaceMolecule


class ChemSpaceFreedomSpaceMoleculeComponent(TableComponent):
    table = ChemSpaceFreedomSpaceMolecule
    display_name = "ChemSpace Freedom"
    description_short = (
        "A vast catalog of commercially available chemical building blocks and "
        "lead-like compounds from ChemSpace. This dataset focuses on the "
        "'Freedom Space'—a collection of billions of accessible molecules for "
        "rapid procurement."
    )
