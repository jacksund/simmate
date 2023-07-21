# -*- coding: utf-8 -*-

from simmate.database.base_data_types import Structure, table_column


class AflowPrototype(Structure):
    """
    A collection of prototype crystal structures from the AFLOW library.

    While this is still a table of structures, this should instead be viewed
    as a table of structure-types. All of the entries in this table come
    from the AFLOW Encyclopedia of Crystallographic Prototypes:
      http://www.aflowlib.org/prototype-encyclopedia/

    Note, while AFLOW licensing does not allow redistribution, all data in this
    table is grabbed directly from `pymatgen`, where the data is under a
    different license. This data does NOT include the entire encyclopedia and
    is therefore out of date. For more info, see
    [pymatgen issue #1446](https://github.com/materialsproject/pymatgen/issues/1446)
    """

    class Meta:
        app_label = "data_explorer"

    archive_fields = [
        "mineral_name",
        "aflow_id",
        "pearson_symbol",
        "strukturbericht_symbol",
        "nsites_wyckoff",
    ]
    api_filters = dict(
        mineral_name=["exact"],
        aflow_id=["exact"],
        pearson_symbol=["exact"],
        strukturbericht_symbol=["exact"],
        nsites_wyckoff=["range"],
    )
    source = "AFLOW Prototypes"
    source_long = (
        "Encyclopedia of Crystallographic Prototypes from the Automatic-FLOW"
        " for Materials Discovery"
    )
    homepage = "http://www.aflowlib.org/prototype-encyclopedia/"
    source_doi = "https://doi.org/10.1016/j.commatsci.2017.01.017"
    remote_archive_link = "https://archives.simmate.org/AflowPrototype-2023-07-06.zip"

    mineral_name = table_column.CharField(max_length=75, blank=True, null=True)
    """
    Common mineral name for this prototype (e.g. "rocksalt"). Note, not all 
    prototypes have this available.
    """

    aflow_id = table_column.CharField(max_length=30)
    """
    Identifier used by the AFLOW library. (e.g. "AB_hP6_154_a_b")
    """

    pearson_symbol = table_column.CharField(max_length=6)
    """
    Pearson symbol for the prototype structure
    """

    strukturbericht_symbol = table_column.CharField(
        max_length=6,
        blank=True,
        null=True,
    )
    """
    Strukturbericht symbol for the prototype structure
    """

    nsites_wyckoff = table_column.IntegerField()
    """
    Number of symmetrically unique wyckoff sites in the prototype structure
    """

    @property
    def name(self):
        """
        This helps piece together the name of the prototype in a user-friendly
        format. We start by checking if there is a mineral_name to use, and we
        also use the prototype's composition.

        An example of a structure with a mineral name is...
            Cinnabar (HgS) Structure-type
        And an example of a structure without a mineral name is..
            CaC6 Structure-type
        """
        if self.mineral_name:
            return f"{self.mineral_name} ({self.formula_reduced}) Structure-type"
        else:
            return f"{self.formula_reduced} Structure-type"

    @property
    def external_link(self) -> str:
        """
        URL to this prototype in the AFLOW website.
        """
        # All COD structures have their data mapped to a URL in the same way
        # ex: http://www.aflowlib.org/prototype-encyclopedia/A2B_hP9_150_ef_bd.html"
        return f"http://www.aflowlib.org/prototype-encyclopedia/{self.aflow_id}.html"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_all_prototypes(cls):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        This method is for pulling AFLOW data into the Simmate database.
        """
        # AFLOW's supported REST API can be accessed via "AFLUX API". This is a separate
        # python package, which is maintained at https://github.com/rosenbrockc/aflow.
        # Note that this not from the official AFLOW team, but it is made such that keywords
        # are pulled dynamically from the AFLOW servers -- any updates in AFLOW's API should
        # be properly handled. Also structures are loaded as ASE Atom objects, which we then
        # convert to pymatgen.

        # This looks like the easiest way to grab all of the data -- as AFLOW doesn't
        # have any good documentation on doing this.
        from pymatgen.analysis.prototypes import AFLOW_PROTOTYPE_LIBRARY
        from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        from rich.progress import track

        # create database objects but don't save them to the database yet
        db_objects = []
        for prototype_data in track(AFLOW_PROTOTYPE_LIBRARY):
            # first let's grab the structure
            structure = prototype_data["snl"].structure

            # To see how many unique wyckoff sites there are we also need the
            # symmetrized structure
            structure_sym = SpacegroupAnalyzer(structure).get_symmetrized_structure()

            # Organize the data into our database format
            new_prototype = cls.from_toolkit(
                structure=structure,
                mineral_name=prototype_data["tags"]["mineral"],
                aflow_id=prototype_data["tags"]["aflow"],
                pearson_symbol=prototype_data["tags"]["pearson"],
                strukturbericht_symbol=prototype_data["tags"]["strukturbericht"],
                nsites_wyckoff=len(structure_sym.wyckoff_symbols),
            )
            db_objects.append(new_prototype)

        # and save it to our database
        cls.objects.bulk_create(
            db_objects,
            batch_size=15000,
            ignore_conflicts=True,
        )
