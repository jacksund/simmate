# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.base import Structure


class OqmdStructure(Structure):

    """ Base Info """

    # OQMD ID
    # For now, max length of 14 is overkill: 'oqmd-123456789'
    id = models.CharField(max_length=14, primary_key=True)

    # Extra data by OQMD's calculations
    final_energy = models.FloatField(blank=True, null=True)
    energy_above_hull = models.FloatField(blank=True, null=True)
    band_gap = models.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check a single entry
    # when scraping data for more (in simmate.database.third_parties.scrapping.aflow)

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "OQMD"

    @property
    def external_link(self):
        # Links to the OQMD dashboard for this structure. An example is...
        #   http://oqmd.org/materials/entry/10435
        id_number = self.id.split("-")[-1]  # this removes the "oqmd-" from the id
        return f"http://oqmd.org/materials/entry/{id_number}"
