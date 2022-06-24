# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


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
        app_label = "third_parties"

    base_info = [
        "structure_string",
        "mineral_name",
        "aflow_id",
        "pearson_symbol",
        "strukturbericht_symbol",
        "nsites_wyckoff",
    ]
    source = "AFLOW Encyclopedia of Crystallographic Prototypes"
    source_doi = "https://doi.org/10.1016/j.commatsci.2017.01.017"
    remote_archive_link = "https://archives.simmate.org/AflowPrototype-2022-06-23.zip"

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

    strukturbericht_symbol = table_column.CharField(max_length=6)
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
