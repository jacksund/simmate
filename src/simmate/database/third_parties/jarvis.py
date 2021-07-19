# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.base import Structure


class JarvisStructure(Structure):

    """ Base Info """

    # Jarvis ID
    # For now, max length of 12 is overkill: 'mp-123456789'
    id = models.CharField(max_length=12, primary_key=True)

    # Extra data by JARVIS's calculations
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    e_above_hull = models.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check the jarvis.json
    # dump file for more:
    #   https://jarvis-materials-design.github.io/dbdocs/thedownloads/

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "JARVIS"
    
    @property
    def external_link(self):
        # All JARVIS structures have their data mapped to a URL in the same way
        # ex: https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/JVASP-1234.xml
        return f"https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/{self.id}.xml"
