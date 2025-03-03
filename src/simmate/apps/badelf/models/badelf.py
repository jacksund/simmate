# -*- coding: utf-8 -*-

from pathlib import Path

import pandas as pd

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)


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

    covalent_algorithm = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The selected algorithm for handling covalent bonds. The defalut is 'zero-flux'
    similar to BadELF's handling of electrides, but 'voronoi' can also be selected
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
    The total number of electrides that were found when searching the maxima
    found using pybader.
    """

    ncovalent_bonds = table_column.FloatField(blank=True, null=True)
    """
    The total number of covalent bonds that were found when searching the maxima
    found using pybader.
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

    elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each atom/electride site
    """

    covalent_atom_pairs = table_column.JSONField(blank=True, null=True)
    """
    A list of atom pairs corresponding to any covalent bonds in the structure
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

    def update_ionic_radii(self, radii: pd.DataFrame):
        # pull all the data together and save it to the database. We
        # are saving this to an ElfIonicRadii datatable. To access this
        # model, we look need to use "ionic_radii.model".
        radius_model = self.ionic_radii.model
        # Let's iterate through the ionic radii and save these to the database.
        for number, row in radii.iterrows():
            site_index = row["site_index"]
            neigh_index = row["neigh_index"]
            radius = row["radius"]
            new_row = radius_model(
                site_index=site_index,
                neigh_index=neigh_index,
                radius=radius,
                bad_elf=self,  # links to this badelf calc
            )
            new_row.save()


class ElfIonicRadii(DatabaseTable):
    """
    This table contains the elf ionic radii calculated during a badelf calculation
    """

    # class Meta:
    #     app_label = "workflows"

    site_index = table_column.IntegerField()
    """
    The index of the central atom that the radius is for
    """
    neigh_index = table_column.IntegerField()
    """
    The index of the neighboring atom
    """
    radius = table_column.FloatField()
    """
    The ELF ionic radius between the central atom and neighbor atom
    """

    """ Relationships """
    # each of these will map to a BadELF calculation, so you should typically access this
    # data through that class.

    # All radii in this table come from a BadELF calculation. There will be
    # many ionic radii linked to a single calculation and they will all be
    # stored together here.
    # Therefore, there's just a simple column stating which badelf calc it
    # belongs to.
    bad_elf = table_column.ForeignKey(
        "BadElf",
        on_delete=table_column.CASCADE,
        related_name="ionic_radii",
    )
