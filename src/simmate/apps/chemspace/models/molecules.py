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
