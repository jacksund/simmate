# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData


class ChemSpaceFreedomSpaceMolecule(ThirdPartyData, Molecule):
    """
    Molecules from the
    [ChemSpace "Freedom Space"](https://chem-space.com/compounds/freedom-space)
    database.
    """

    class Meta:
        db_table = "chemspace__freedom_space__molecules"

    # TODO: Freedom space is now 5bil molecules... The "Screening Compound Catalog"
    # is now what we'd want. It is roughly 7.5mil compounds:
    #   https://chem-space.com/compounds#screening-compounds

    html_display_name = "ChemSpace Freedom"
    html_description_short = (
        "A vast catalog of commercially available chemical building blocks and "
        "lead-like compounds from ChemSpace. This dataset focuses on the "
        "'Freedom Space'—a collection of billions of accessible molecules for "
        "rapid procurement."
    )
    is_redistribution_allowed = False

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
