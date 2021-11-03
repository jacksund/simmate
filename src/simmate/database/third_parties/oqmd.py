# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class OqmdStructure(Structure):

    # The id used to symbolize the structure.
    # For example, Materials Project structures are represented by ids such as
    # "mp-12345" while AFLOW structures by "aflow-12345"
    id = table_column.CharField(max_length=25, primary_key=True)

    """ Base Info """

    # Extra data by OQMD's calculations
    final_energy = table_column.FloatField(blank=True, null=True)
    energy_above_hull = table_column.FloatField(blank=True, null=True)
    band_gap = table_column.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check a single entry
    # when scraping data for more (in simmate.database.third_parties.scrapping.aflow)

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "OQMD"

    # Make sure Django knows which app this is associated with
    class Meta:
        app_label = "third_parties"

    @property
    def external_link(self):
        # Links to the OQMD dashboard for this structure. An example is...
        #   http://oqmd.org/materials/entry/10435
        id_number = self.id.split("-")[-1]  # this removes the "oqmd-" from the id
        return f"http://oqmd.org/materials/entry/{id_number}"
