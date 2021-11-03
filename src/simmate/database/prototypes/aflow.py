# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class AflowPrototype(Structure):

    # While this is still a table of structures, this should instead be viewed
    # as a table of structure-types. All of the entries in this table come
    # from the AFLOW Encyclopedia of Crystallographic Prototypes:
    #   http://www.aflowlib.org/prototype-encyclopedia/

    """Base Info"""

    mineral_name = table_column.CharField(max_length=75, blank=True, null=True)
    aflow_id = table_column.CharField(max_length=30)
    pearson_symbol = table_column.CharField(max_length=6)
    strukturbericht = table_column.CharField(max_length=6)
    nsites_wyckoff = table_column.IntegerField()

    """ Model Methods """

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

    """ Django App Association """

    class Meta:
        app_label = "prototypes"
