# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure, Thermodynamics


class MaterialsProjectStructure(Structure, Thermodynamics):

    # The id used to symbolize the structure (ex: "mp-12345")
    id = table_column.CharField(max_length=25, primary_key=True)

    source = "Materials Project"

    @property
    def external_link(self):
        # All Materials Project structures have their data mapped to a URL in
        # the same way. For example...
        #   https://materialsproject.org/materials/mp-12345/
        return f"https://materialsproject.org/materials/{self.id}/"

    @classmethod
    def from_pymatgen(
        cls,
        id,
        structure,
        energy,
        as_dict=False,
    ):
        # because this is a combination of tables, I need to build the data for
        # each and then feed all the results into this class

        # first grab the full dictionaries for each parent model
        thermo_data = Thermodynamics.from_base_data(
            structure,
            energy,
            as_dict=True,
        )
        structure_data = Structure.from_pymatgen(structure, as_dict=True)

        # Now feed all of this dictionarying into one larger one.
        all_data = dict(
            id=id,
            **structure_data,
            **thermo_data,
        )

        # If as_dict is false, we build this into an Object. Otherwise, just
        # return the dictionary
        return all_data if as_dict else cls(**all_data)

    # Make sure Django knows which app this is associated with
    class Meta:
        app_label = "third_parties"
