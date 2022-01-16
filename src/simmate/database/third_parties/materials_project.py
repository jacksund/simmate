# -*- coding: utf-8 -*-

from pymatgen.core import Structure as PMGStructure

from simmate.database.base_data_types import table_column, Structure, Thermodynamics


class MatProjStructure(Structure, Thermodynamics):
    class Meta:
        # Make sure Django knows which app this is associated with
        app_label = "third_parties"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "mp-12345")
    """

    source = "Materials Project"
    """
    Where this structure and data came from
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the Materials Project webstite.
        """
        # All Materials Project structures have their data mapped to a URL in
        # the same way. For example...
        #   https://materialsproject.org/materials/mp-12345/
        return f"https://materialsproject.org/materials/{self.id}/"

    @classmethod
    def from_toolkit(
        cls,
        id: str,
        structure: PMGStructure,
        energy: float,
        as_dict: bool = False,
    ):
        """
        Builds the full database entry from a structure and energy. Can return as
        a MatProjStructure object or an expanded dictionary.

        Parameters
        ----------
        - `id`:
            The Materials Project ID (ex: "mp-12345")
        - `structure`:
            DESCRIPTION.
        - `energy`:
            The final calculated energy (in eV).
        as_dict :
            Where to return an initialized object or just an expanded dictionary.
            The default is False.
        """

        # because this is a combination of tables, I need to build the data for
        # each and then feed all the results into this class

        # first grab the full dictionaries for each parent model
        thermo_data = Thermodynamics.from_toolkit(
            structure,
            energy,
            as_dict=True,
        )
        structure_data = Structure.from_toolkit(
            structure,
            as_dict=True,
        )

        # Now feed all of this dictionarying into one larger one.
        all_data = dict(
            id=id,
            **structure_data,
            **thermo_data,
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)
