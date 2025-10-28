# -*- coding: utf-8 -*-

from pathlib import Path

import pandas as pd

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)

class SpinBadElf(Structure, Calculation):
    """
    Contains results from a spin-separated BadELF analysis
    """
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this BadELF calculation
    """
    
    badelf_up = table_column.ForeignKey(
        "BadElf",
        on_delete=table_column.CASCADE,
        related_name="spin_bad_elf",
    )
    
    badelf_down = table_column.ForeignKey(
        "BadElf",
        on_delete=table_column.CASCADE,
        related_name="spin_bad_elf",
    )
    

class BadElf(Structure, Calculation):
    """
    This table contains results from a BadELF analysis.
    """
    
    method_kwargs = table_column.JSONField(blank=True, null=True)
    """
    The settings used for this BadELF calculation
    """

    oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    The oxidation states for each atom and electride in the system.
    """

    charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom and electride
    feature in the system (i.e. electride/covelent bond etc.)
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    min_surface_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom or electride 
    to the bader/plane surface.
    """
    
    avg_surface_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of average distances from the origin of an atom or electride 
    to the bader/plane surface.
    """

    volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of atom or electride volumes from the oxidation analysis
    """
    
    electride_indices = table_column.JSONField(blank=True, null=True)
    """
    The indices in each entry (e.g. charges, volumes) that correspond
    to electrides
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

    electride_dim = table_column.JSONField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure. Gives
    all dimensionalities that exist at varying ELF values.
    """

    electride_dim_cutoffs = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality.
    """

    coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms and electrides in the
    labeled structure
    """

    elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each atom and electride
    in the labeled structure
    """

    separate_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the user asked to consider spin separately in this calculation
    """

    differing_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the spin up and spin down differ in the ELF and charge density
    """

    electride_structure = table_column.JSONField(blank=True, null=True)
    """
    A PyMatGen Structure JSON with dummy atoms (E) representing electrides.
    """

    elf_analysis = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="badelf",
    )
    """
    The ElfAnalysis table entry from this calculation which includes
    more detailed information on each chemical feature found in the
    system.
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
        if radii is not None:
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
