# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, Thermodynamics, table_column


class AflowStructure(Structure, Thermodynamics):
    """
    Crystal structures from the [AFLOW](http://aflowlib.org/) database.

    Currently, this table only stores strucure and thermodynamic information,
    but the AFLOW has much more data available via their
    [REST API](http://aflowlib.duke.edu/aflowwiki/doku.php?id=documentation:start)
    and website.
    """

    class Meta:
        db_table = "aflow__structures"

    html_display_name = "AFLOW"
    html_description_short = "The Automatic-FLOW for Materials Discovery"

    external_website = "http://www.aflowlib.org/"
    source_doi = "https://doi.org/10.1016/j.commatsci.2012.02.005"
    is_redistribution_allowed = False

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

    # -------------------------------------------------------------------------

    def load_source_data(cls):
        """
        Loads all structures directly for the AFLOW database into the local
        Simmate database.

        AFLOW's supported REST API can be accessed via the AFLUX API:
            - https://aflow.org/API/aflux/

        Note, there is a separate python package, which is maintained at
        https://github.com/rosenbrockc/aflow. However, this has not been updated
        since 2020, and it is not from the official AFLOW team. We opt to use
        connect to the AFLUX REST API directly
        """
        raise NotImplementedError()
        # This is a list of the supported "catalogs" that AFLOW has -- which appear
        # to be separately stored databases.
        # catalog=[
        #     "icsd",  # 60,000 structures
        #     "lib1",  # 4,000 structures
        #     "lib2",  # 360,000 structures (binary phases)
        #     "lib3",  # 2,530,000 structures (ternary phases)
        # ]

        # you get the list of structures using:
        #   https://aflow.org/API/aflux/?catalog(icsd)

        # available props can be pulled from:
        #   https://aflow.org/API/aflux/?help(properties)

        # once you have the props list that you want, you can grab them using
        # a comma separated list:
        #   https://aflow.org/API/aflux/?catalog(icsd),auid,spacegroup_relax,compound,aflow_prototype_label_relax

        # structures are not available in the AFLUX api, but we use the ID/url
        # to switch over to the main site and download the file:
        # https://aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/MCLC/Al1Li1O6Si2_ICSD_159530/CONTCAR.relax.vasp
        # or
        # https://aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/MCLC/Al1Li1O6Si2_ICSD_159530/CONTCAR.relax.qe
