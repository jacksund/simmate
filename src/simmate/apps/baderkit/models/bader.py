 # -*- coding: utf-8 -*-

from .base import BaderkitBase
from simmate.database.base_data_types import table_column

class Bader(BaderkitBase):
    """
    This table contains results from a Bader charge analysis run using
    the BaderKit package.
    """

    class Meta:
        app_label = "baderkit"

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each site.
    """

    atom_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each site.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    atom_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of site volumes from the oxidation analysis (i.e. the bader volume)
    """

    atom_min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The minimum distance from each atom to its partitioning surface.
    """

    atom_avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The average distance from each atom to the points on its partitioning
    surface
    """

    maxima_frac = table_column.JSONField(blank=True, null=True)
    """
    The fractional coordinates of each basin maximum
    """

    maxima_charge_values = table_column.JSONField(blank=True, null=True)
    """
    The value of the charge density at each basin maximum
    """

    maxima_ref_values = table_column.JSONField(blank=True, null=True)
    """
    The value of the reference grid at each basin maximum
    """

    basin_charges = table_column.JSONField(blank=True, null=True)
    """
    The charge associated with each bader basin.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation.
    """

    basin_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of basin volumes from the oxidation analysis (i.e. the bader volume)
    """

    basin_min_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The minimum distance from each basin maximum to its partitioning surface.
    """

    basin_avg_surface_distances = table_column.JSONField(blank=True, null=True)
    """
    The average distance from each basin maximum to the points on its partitioning
    surface
    """

    basin_atoms = table_column.JSONField(blank=True, null=True)
    """
    The atom site indices each basin is assigned to
    """

    basin_atom_dists = table_column.JSONField(blank=True, null=True)
    """
    The distance from each basin's maximum to the site it is assigned to
    """

    total_electron_number = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

