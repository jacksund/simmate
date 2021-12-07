# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class JarvisStructure(Structure):

    """Base Info"""

    # The id used to symbolize the structure.
    # For example, Materials Project structures are represented by ids such as
    # "mp-12345" while AFLOW structures by "aflow-12345"
    id = table_column.CharField(max_length=25, primary_key=True)

    # Extra data by JARVIS's calculations
    formation_energy_per_atom = table_column.FloatField(blank=True, null=True)
    energy_above_hull = table_column.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check the jarvis.json
    # dump file for more:
    #   https://jarvis-materials-design.github.io/dbdocs/thedownloads/

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "JARVIS"

    # Make sure Django knows which app this is associated with
    class Meta:
        app_label = "third_parties"

    @property
    def external_link(self):
        # All JARVIS structures have their data mapped to a URL in the same way
        # ex: https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/JVASP-1234.xml
        # we store the id as "jvasp-123" so we need to convert this to uppercase
        id = self.id.upper()
        return f"https://www.ctcms.nist.gov/~knc6/static/JARVIS-DFT/{id}.xml"
