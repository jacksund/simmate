# -*- coding: utf-8 -*-

from django.db import models

from simmate.database.structure import Structure


class JarvisStructure(Structure):

    """ Base Info """

    # Extra data by JARVIS's calculations
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    energy_above_hull = models.FloatField(blank=True, null=True)
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
        # we store the id as "jvasp-123" so we need to convert this to uppercase
        id = self.id.upper()
        return f"https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/{id}.xml"
