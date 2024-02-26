# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.database.base_data_types import Calculation, Structure, table_column


class BadElf(Structure, Calculation):
    """
    This table contains results from a BadELF analysis.
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    A list of calculated oxidation states for each site.
    """

    algorithm = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The selected algorithm. The default is BadELF as defined by the warren lab:
    https://pubs.acs.org/doi/10.1021/jacs.3c10876
    However, a more traditional Zero-flux surface type algorithm can be used as well.
    """

    charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each site.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    min_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum radii distance for bader volumes. i.e. the minimum
    distance from the origin of the site to the bader surface. This can be used
    as a minimum radius for the site.
    """

    atomic_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of site volumes from the oxidation analysis (i.e. the bader volume)
    """

    element_list = table_column.JSONField(blank=True, null=True)
    """
    A list of all element species in order that appear in the structure.
    
    This information is stored in the 'structure' column as well, but it is 
    stored here as an extra for convenience.
    """

    vacuum_charge = table_column.FloatField(blank=True, null=True)
    """
    Total electron count that was NOT assigned to ANY site -- and therefore
    assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    vacuum_volume = table_column.FloatField(blank=True, null=True)
    """
    Total volume from electron density that was NOT assigned to ANY site -- 
    and therefore assigned to 'vacuum'.
    
    In most cases, this value should be zero.
    """

    nelectrons = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons involved in the charge density partitioning.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    electrides_per_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    formula unit.
    """

    electrides_per_reduced_formula = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons assigned to electride sites for this structures
    reduced formula unit.
    """

    nelectrides = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the BCF.dat
    file in some BadELF or Bader workflows.
    """

    electride_dim = table_column.JSONField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure. Defaults to
    the highest dimension network.
    """

    dim_cutoffs = table_column.JSONField(blank=True, null=True)
    """
    The ELF value cutoff used to determine if two electride sites are connected.
    Used to determine the dimensionality of the electride electron network.
    """

    coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms and electrides in the
    structure
    """

    def write_output_summary(self, directory: Path):
        super().write_output_summary(directory)

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass
