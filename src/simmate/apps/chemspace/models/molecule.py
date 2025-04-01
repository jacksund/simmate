# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column


class ChemSpaceFreedom(Molecule):
    """
    Molecules from the
    [ChemSpace "Freedom Space"](https://chem-space.com/compounds/freedom-space)
    database.
    """

    # TODO: Freedom space is now 5bil molecules... The "Screening Compound Catalog"
    # is now what we'd want. It is roughly 7.5mil compounds:
    #   https://chem-space.com/compounds#screening-compounds

    # disable cols
    source = None

    html_display_name = "ChemSpace Freedom"
    html_description_short = (
        "A diverse set of 201M compounds, 73% of which comply with Ro5."
    )

    external_website = "https://chem-space.com/compounds/freedom-space"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the molecule (ex: "a1_101109_29635")
    """
    # BUG: this is catalog number, but we really want ChemSpaceID

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the ChemSpace website.
        """
        return f"https://chem-space.com/{self.chemspace_id}"
