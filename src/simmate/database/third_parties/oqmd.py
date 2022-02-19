# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure, Thermodynamics


class OqmdStructure(Structure, Thermodynamics):
    """
    Crystal structures from the [OQMD](http://oqmd.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but OQDMD has much more data available via their
    [REST API](http://oqmd.org/static/docs/restful.html) and website.
    """

    class Meta:
        app_label = "third_parties"

    base_info = ["id", "structure_string", "energy"]
    source = "OQMD"
    source_doi = "https://doi.org/10.1007/s11837-013-0755-4"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "oqmd-12345")
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the OQMD website.
        """
        # Links to the OQMD dashboard for this structure. An example is...
        #   http://oqmd.org/materials/entry/10435
        id_number = self.id.split("-")[-1]  # this removes the "oqmd-" from the id
        return f"http://oqmd.org/materials/entry/{id_number}"
