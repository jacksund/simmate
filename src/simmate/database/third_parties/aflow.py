# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.base import Structure


class AflowStructure(Structure):

    """ Base Info """

    # Jarvis ID
    # For now, max length of 30 is overkill: 'aflow-abcdefghijklmnopqrstuvwx'
    id = models.CharField(max_length=30, primary_key=True)

    # Extra data by JARVIS's calculations
    final_energy = models.FloatField(blank=True, null=True)
    final_energy_per_atom = models.FloatField(blank=True, null=True)
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    band_gap = models.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check a single entry
    # when scraping data for more (in simmate.database.third_parties.scrapping.aflow)
    
    # The hull energy of the structure is not supported by this databse, but
    # we have enough information here to generate this value ourselves. We
    # therefore have this field empty to start and we then calculate it in Simmate.
    energy_above_hull = models.FloatField(blank=True, null=True)
    
    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "AFLOW"

    @property
    def external_link(self):
        # Links to the AFLOW dashboard for this structure. An example is...
        #   http://aflow.org/material/?id=aflow:ffea9279661c929f
        # !!! I could also consider an alternative link which points to an interactive
        # REST endpoint. The API is also sporatic for these, An example one is...
        #   aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/FCC/Dy1Mn2_ICSD_602151
        id_formatted = self.id.replace("-",":")
        return f"http://aflow.org/material/?id={id_formatted}"

    """ Model Methods """

    @classmethod
    def from_dict(cls, data_dict):

        # initialize this model object using the data. I pass to super() method to
        # handle the "structure". The reason I even have this method is because
        # there's a bunch of extra kwargs I'm passing in along with "structure".
        structure_db = super().from_pymatgen(**data_dict)

        return structure_db
