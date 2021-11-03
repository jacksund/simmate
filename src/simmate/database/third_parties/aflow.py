# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, Structure


class AflowStructure(Structure):

    # The id used to symbolize the structure.
    # For example, Materials Project structures are represented by ids such as
    # "mp-12345" while AFLOW structures by "aflow-12345"
    id = table_column.CharField(max_length=25, primary_key=True)

    """Base Info"""

    # Extra data by JARVIS's calculations
    final_energy = table_column.FloatField(blank=True, null=True)
    final_energy_per_atom = table_column.FloatField(blank=True, null=True)
    formation_energy_per_atom = table_column.FloatField(blank=True, null=True)
    band_gap = table_column.FloatField(blank=True, null=True)
    # !!! There are plenty more properties I can add too. Check a single entry
    # when scraping data for more (in simmate.database.third_parties.scrapping.aflow)

    # The hull energy of the structure is not supported by this databse, but
    # we have enough information here to generate this value ourselves. We
    # therefore have this field empty to start and we then calculate it in Simmate.
    energy_above_hull = table_column.FloatField(blank=True, null=True)

    """ Properties """

    # OPTIMIZE: is it better to just set the attribute than to have a fixed
    # property that's defined via a function?
    source = "AFLOW"

    # Make sure Django knows which app this is associated with
    class Meta:
        app_label = "third_parties"

    @property
    def external_link(self):
        # Links to the AFLOW dashboard for this structure. An example is...
        #   http://aflow.org/material/?id=aflow:ffea9279661c929f
        # !!! I could also consider an alternative link which points to an interactive
        # REST endpoint. The API is also sporatic for these, An example one is...
        #   aflowlib.duke.edu/AFLOWDATA/ICSD_WEB/FCC/Dy1Mn2_ICSD_602151
        id_formatted = self.id.replace("-", ":")
        return f"http://aflow.org/material/?id={id_formatted}"

    """ Model Methods """

    @classmethod
    def from_dict(cls, data_dict):

        # initialize this model object using the data. I pass to super() method to
        # handle the "structure". The reason I even have this method is because
        # there's a bunch of extra kwargs I'm passing in along with "structure".
        structure_db = super().from_pymatgen(**data_dict)

        return structure_db
