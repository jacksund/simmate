# -*- coding: utf-8 -*-

from pymatgen.io.ase import AseAtomsAdaptor
from rich.progress import track

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

    # disable cols
    source = None

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

    @classmethod
    def _load_all_structures(cls):
        """
        Only use this function if you are part of the Simmate dev team!

        Loads all structures directly for the AFLOW database into the local
        Simmate database.

        AFLOW's supported REST API can be accessed via "AFLUX API". This is a separate
        python package, which is maintained at https://github.com/rosenbrockc/aflow.
        Note that this not from the official AFLOW team, but it is made such that keywords
        are pulled dynamically from the AFLOW servers -- any updates in AFLOW's API should
        be properly handled. Also structures are loaded as ASE Atom objects, which we then
        convert to pymatgen.
        """

        # AFLOW is not a dependency of simmate, so make sure you install it before using
        # this module
        try:
            from aflow import K as AflowKeywords
            from aflow.control import Query as AflowQuery
        except:
            raise ModuleNotFoundError(
                "You must install aflow client with `conda install -c conda-forge aflow`"
            )

        # The way we build a query looks similar to the Django API, where we start
        # with a Query object (similar to Table.objects manager) and build filters
        # off of it.
        data = (
            AflowQuery(
                # This is a list of the supported "catalogs" that AFLOW has -- which appear
                # to be separately stored databases. I just use all of them by default.
                catalog=[
                    "icsd",  # 60,000 structures
                    "lib1",  # 4,000 structures
                    "lib2",  # 360,000 structures (binary phases)
                    "lib3",  # 2,530,000 structures (ternary phases)
                ],
                # The batch size the number of results to return per HTTP request.
                batch_size=2000,
            )
            # .filter(
            #     # Now we want set the conditions for which structures to pull. Because we
            #     # want all of them, we normally comment this line out. For testing, we
            #     # can pull a smaller subset of the structures.
            #     # I use the element Dy because it gives about 1,300 structures
            #     AflowKeywords.species == "Dy",
            # )
            .select(
                # Indicate what data we want to grab from each result. Note that we don't
                # access the structure quite yet.
                AflowKeywords.auid,
                # This is the URL that leads to the rest of the data. Note it is a
                # interactive REST endpoint, while the dashboard link is different.
                # AflowKeywords.aurl,
                # The date that the entry was added
                # AflowKeywords.aflowlib_date,
                # Band gap
                # AflowKeywords.Egap,
                # The calculated energy of the unit cell
                AflowKeywords.enthalpy_cell,
                # BUG: or should we use energy_cell? Aren't these the same in
                # groundstate DFT?
            )
        )

        # Let's sanitize all structures first. So iterate through each one in the list
        # This also takes a while, so we use a progress bar
        for entry in track(data):
            # grab the structure -- this is loaded as an ASE atoms object
            structure_ase = entry.atoms()

            # convert the structure to pymatgen
            structure_pmg = AseAtomsAdaptor.get_structure(structure_ase)

            # now convert the entry to a database object
            structure_db = cls.from_toolkit(
                id=entry.auid.replace(":", "-"),
                structure=structure_pmg,
                energy=entry.enthalpy_cell,
            )

            # and save it to our database!
            structure_db.save()
