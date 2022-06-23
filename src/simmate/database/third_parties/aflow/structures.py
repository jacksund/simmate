# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure, Thermodynamics


class AflowStructure(Structure, Thermodynamics):
    """
    Crystal structures from the [AFLOW](http://aflowlib.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but the AFLOW has much more data available via their
    [REST API](http://aflowlib.duke.edu/aflowwiki/doku.php?id=documentation:start)
    and website.
    """

    class Meta:
        app_label = "third_parties"

    base_info = ["id", "structure_string", "energy"]
    source = "AFLOW"
    source_doi = "https://doi.org/10.1016/j.commatsci.2012.02.005"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The id used to represent the structure (ex: "aflow-12345")
    """

    @property
    def external_link(self) -> str:
        """
        URL to this structure in the AFLOW website.
        """
        # Links to the AFLOW dashboard for this structure. An example is...
        #   http://aflow.org/material/?id=aflow:ffea9279661c929f
        # !!! I could also consider an alternative link which points to an interactive
        # REST endpoint. The API is also sporatic for these, An example one is...
        #   aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/FCC/Dy1Mn2_ICSD_602151
        id_formatted = self.id.replace("-", ":")
        return f"http://aflow.org/material/?id={id_formatted}"
