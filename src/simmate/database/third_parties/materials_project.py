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

    """ Model Methods """

    # TODO: This should be an ETL workflow (maybe no L?). I can link to the
    # workflow in the future when it's ready
    # @classmethod
    # def from_query(criteria, api_key="2Tg7uUvaTAPHJQXl"):
    #     some_workflow.run()

    @classmethod
    def from_dict(cls, data_dict):
        # the dictionary format follows what is returned by the MPRester query,
        # which has requested the following properties:
        #   properties = [
        #       "material_id",
        #       "final_energy",
        #       "final_energy_per_atom",
        #       "formation_energy_per_atom",
        #       "e_above_hull",
        #       "structure",
        #       "band_gap",
        #   ]

        # For full compatibility with django, we need to rename the material_id
        # to just id. Also since I'm changing things in place, I need to make a
        # copy of the dict as well.
        data = data_dict.copy()
        data["id"] = data.pop("material_id")

        # initialize this model object using the data. I pass to super() method to
        # handle the "structure". The reason I even have this method is because
        # there's a bunch of extra kwargs I'm passing in along with "structure".
        structure_db = super().from_pymatgen(**data)

        return structure_db
