# -*- coding: utf-8 -*-

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
