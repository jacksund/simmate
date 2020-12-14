# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from django.db import models

# TYPES OF RELATIONSHIPS:
# ManyToMany - place in either but not both
# ManyToOne (ForeignKey) - place in the many
# OneToOne  - place in the one that has extra features (it's like setting a parent class)

# --------------------------------------------------------------------------------------


class Structure(models.Model):

    """ Base info """

    # The formatted formula of the structure for convenience
    pretty_formula = models.CharField(max_length=25)

    # total number of sites in the unitcell
    nsites = models.IntegerField()

    # Density of the structure for convenience
    density = models.FloatField()

    # The structure which is written as a json string from pymatgen's to_json method.
    # To convert back to Structure object, you need to apply json.loads to the string
    # and then Structure.from_dict
    #!!! Postgres does support a dictionary type, but we don't use that here so that
    #!!! we can still test with SQLite3
    structure = models.TextField()

    #!!! In the future, Materials Project info will be better off in a separate table.
    #!!! This is because not all structures will be from the Materials Project.

    # Materials Project ID
    # Max length of 12 is overkill: 'mp-123456789'
    material_id = models.CharField(max_length=12)

    # Final calculated energy by Materials Project
    # Because Materials Project may be missing some of these values or we may add a
    # structure without a calc done, we set this column as optional.
    final_energy = models.FloatField(blank=True, null=True)
    final_energy_per_atom = models.FloatField(blank=True, null=True)
    formation_energy_per_atom = models.FloatField(blank=True, null=True)
    e_above_hull = models.FloatField(blank=True, null=True)

    """ Relationships """
    # Each structure will have many DiffusionPathway(s)

    """ Properties """
    """ Model Methods """
    # none implemented yet

    """ Restrictions """
    # none

    """ For website compatibility"""

    class Meta:
        app_label = "diffusion"


class Pathway(models.Model):

    """ Base info """

    # The element of the diffusion atom
    # Note: do not confuse this with ion, which has charge
    element = models.CharField(max_length=2)

    # The expected index in DistinctPathFinder.get_paths. The shortest path is index 0.
    # index is a reserved keyword so I need to use dpf_index
    dpf_index = models.IntegerField()

    # The length/distance of the pathway from start to end (linear measurement)
    distance = models.FloatField()

    # the initial, midpoint, and end site fractional coordinates
    # Really, this is a list of float values, but I save it as a string.
    #!!! for robustness, should I save cartesian coordinates and/or lattice as well?
    #!!! Does the max length make sense here and below?
    #!!! Consider switch msite to image in the future.
    isite = models.CharField(max_length=100)
    msite = models.CharField(max_length=100)
    esite = models.CharField(max_length=100)

    """ Relationships """
    # Each Pathway corresponds to one Structure, which can have many Pathway(s)
    structure = models.ForeignKey(
        Structure,
        on_delete=models.CASCADE,
        related_name="pathways",
    )

    # Each Pathway will map to a row in the PathwayCalcs table. I keep this separate
    # for organization, though I could also move it here if I'd like

    """ Properties """
    """ Model Methods """
    # none implemented yet

    """ Restrictions """
    # none

    """ For website compatibility"""

    class Meta:
        app_label = "diffusion"


class PathwayCalc(models.Model):

    """ Base info """

    #

    """ Relationships """
    # Each PathwayCalcs corresponds to one Pathway, which can have many Pathway(s)
    # I set primary_key to true so that the primary keys match that of the pathway
    pathway = models.OneToOneField(Pathway, primary_key=True, on_delete=models.CASCADE)

    # Each Pathway will map to a row in the PathwayCalcs table. I keep this separate
    # for organization, though I could also move it here if I'd like

    """ Properties """
    """ Model Methods """
    # none implemented yet

    """ Restrictions """
    # none

    """ For website compatibility"""

    class Meta:
        app_label = "diffusion"
