# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.base import Structure


class MaterialsProjectStructure(Structure):

    """ Base Info """

    # Materials Project ID
    # For now, max length of 12 is overkill: 'mp-123456789'
    id = models.CharField(max_length=12, primary_key=True)

    # Final calculated energy by Materials Project
    # Because Materials Project may be missing some of these values or we may add a
    # structure without a calc done, we set this column as optional.
    # TODO: should this be located in a Calculation relationship?
    final_energy = models.FloatField(blank=True, null=True)
    final_energy_per_atom = models.FloatField(blank=True, null=True)
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    e_above_hull = models.FloatField(blank=True, null=True)
    band_gap = models.FloatField(blank=True, null=True)
    # band_gap__is_direct = models.BooleanField(blank=True, null=True)
    # !!! There are plenty more properties I can add to:
    #   https://github.com/materialsproject/mapidoc/tree/master/materials

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "Materials Project"

    @property
    def external_link(self):
        # All Materials Project structures have their data mapped to a URL in 
        # the same way. For example...
        #   https://materialsproject.org/materials/mp-12345/
        return f"https://materialsproject.org/materials/{self.id}/"
