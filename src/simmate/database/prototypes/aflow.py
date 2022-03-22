# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class AflowPrototype(Structure):
    """
    A collection of prototype crystal structures from the AFLOW library.

    While this is still a table of structures, this should instead be viewed
    as a table of structure-types. All of the entries in this table come
    from the AFLOW Encyclopedia of Crystallographic Prototypes:
      http://www.aflowlib.org/prototype-encyclopedia/
    """

    class Meta:
        app_label = "prototypes"

    base_info = [
        "structure_string",
        "mineral_name",
        "aflow_id",
        "pearson_symbol",
        "strukturbericht",
        "nsites_wyckoff",
    ]
    source = "AFLOW Encyclopedia of Crystallographic Prototypes"
    source_doi = "https://doi.org/10.1016/j.commatsci.2017.01.017"
    # remote_archive_link = "TODO"  # also this will be private due to AFLOW licensing

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

    strukturbericht = table_column.CharField(max_length=6)
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
