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

    atom_oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    In systems with non-atomic elf features, this provides the oxidation
    states for just the atoms.
    """

    electride_oxidation_states = table_column.JSONField(blank=True, null=True)
    """
    In systems with non-atomic elf features, this provides the oxidation
    states for just the electrides.
    """

    electride_oxidation_states_up = table_column.JSONField(blank=True, null=True)
    """
    In systems with non-atomic elf features, this provides the oxidation
    states for just the electrides in the spin-up system.
    """

    electride_oxidation_states_down = table_column.JSONField(blank=True, null=True)
    """
    In systems with non-atomic elf features, this provides the oxidation
    states for just the electrides in the spin-down system.
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

    shared_feature_algorithm = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The selected algorithm for handling covalent/metallic bonds. The defalut is 'zero-flux'
    similar to BadELF's handling of electrides, but 'voronoi' can also be selected
    """

    shared_feature_separation_method = table_column.CharField(
        blank=True,
        null=True,
        max_length=75,
    )
    """
    The selected algorithm for dividing charge in covalent/metallic bonds.
    """

    atom_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each site.
    
    WARNING: this count is dependent on the potentials used. For example, 
    Yttrium could have used a potential where 2 or even 10 electrons are used 
    as the basis for the calculation. Use 'oxidation_states' for a more 
    consistent and accurate count of valence electrons
    """

    atom_charges_up = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom in the
    spin-up system
    """

    atom_charges_down = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each atom in the
    spin-down system
    """

    electride_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each electride in the
    total system
    """

    electride_charges_up = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each electride in the
    spin-up system
    """

    electride_charges_down = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each electride in the
    spin-down system
    """

    shared_feature_charges = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each covalent/metallic
    feature in the total system
    """

    shared_feature_charges_up = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each covalent/metallic
    feature in the spin-up system
    """

    shared_feature_charges_down = table_column.JSONField(blank=True, null=True)
    """
    A list of total "valence" electron counts for each covalent/metallic
    feature in thespin-down system
    """

    atom_min_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom to the
    bader/plane surface.
    """

    atom_min_dists_up = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom to the
    bader/plane surface for the spin-up system.
    """

    atom_min_dists_down = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an atom to the
    bader/plane surface for the spin-down system.
    """

    electride_min_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an electride to the
    bader/plane surface.
    """

    electride_min_dists_up = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an electride to the
    bader/plane surface for the spin-up system.
    """

    electride_min_dists_down = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an electride to the
    bader/plane surface for the spin-down system.
    """

    shared_feature_min_dists = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an shared_feature to the
    bader/plane surface.
    """

    shared_feature_min_dists_up = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an shared_feature to the
    bader/plane surface for the spin-up system.
    """

    shared_feature_min_dists_down = table_column.JSONField(blank=True, null=True)
    """
    A list of minimum distances from the origin of an shared_feature to the
    bader/plane surface for the spin-down system.
    """

    atom_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of atom volumes from the oxidation analysis
    """

    atom_volumes_up = table_column.JSONField(blank=True, null=True)
    """
    A list of atom volumes for the spin-up system
    """

    atom_volumes_down = table_column.JSONField(blank=True, null=True)
    """
    A list of atom volumes for the spin-down system
    """

    electride_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of electride volumes from the oxidation analysis
    """

    electride_volumes_up = table_column.JSONField(blank=True, null=True)
    """
    A list of electride volumes for the spin-up system
    """

    electride_volumes_down = table_column.JSONField(blank=True, null=True)
    """
    A list of electride volumes for the spin-down system
    """

    shared_feature_volumes = table_column.JSONField(blank=True, null=True)
    """
    A list of shared_feature volumes from the oxidation analysis
    """

    shared_feature_volumes_up = table_column.JSONField(blank=True, null=True)
    """
    A list of shared_feature volumes for the spin-up system
    """

    shared_feature_volumes_down = table_column.JSONField(blank=True, null=True)
    """
    A list of shared_feature volumes for the spin-down system
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

    vacuum_volume_up = table_column.FloatField(blank=True, null=True)
    """
    Total volume from electron density that was NOT assigned to ANY site -- 
    and therefore assigned to 'vacuum' in the spin-up system.
    
    In most cases, this value should be zero.
    """

    vacuum_volume_down = table_column.FloatField(blank=True, null=True)
    """
    Total volume from electron density that was NOT assigned to ANY site -- 
    and therefore assigned to 'vacuum' in the spin-down system.
    
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

    nelectrons_up = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons in the spin-up charge density
    """

    nelectrons_down = table_column.FloatField(blank=True, null=True)
    """
    The total number of electrons in the spin-down charge density
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

    nelectrides_up = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the maxima
    of the spin-up ELF
    """

    nelectrides_down = table_column.IntegerField(blank=True, null=True)
    """
    The total number of electrides that were found when searching the maxima
    of the spin-down ELF
    """

    nshared_features = table_column.FloatField(blank=True, null=True)
    """
    The total number of shared ELF features that were found. This includes
    covalent bonds, metallic features, and non-electridic bare electrons.
    """

    electride_dim = table_column.JSONField(blank=True, null=True)
    """
    The dimensionality of the electride network in the structure. Gives
    all dimensionalities that exist at varying ELF values.
    """

    electride_dim_up = table_column.JSONField(blank=True, null=True)
    """
    The dimensionality of the electride network in the spin-up system. 
    Gives all dimensionalities that exist at varying ELF values.
    """

    electride_dim_down = table_column.JSONField(blank=True, null=True)
    """
    The dimensionality of the electride network in the spin-down system. 
    Gives all dimensionalities that exist at varying ELF values.
    """

    electride_dim_cutoffs = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality.
    """

    electride_dim_cutoffs_up = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality
    in the spin-up system
    """

    electride_dim_cutoffs_down = table_column.JSONField(blank=True, null=True)
    """
    The ELF values at which the bare electron volume reduces dimensionality
    in the spin-down system
    """

    atom_coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms in the
    labeled structure
    """

    atom_coord_envs_up = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms in the
    spin-up labeled structure
    """

    atom_coord_envs_down = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the atoms in the
    spin-down labeled structure
    """

    electride_coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the electrides in the
    labeled structure
    """

    electride_coord_envs_up = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the electrides in the
    spin-up labeled structure
    """

    electride_coord_envs_down = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the electrides in the
    spin-down labeled structure
    """

    shared_feature_coord_envs = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the shared_features in the
    labeled structure
    """

    shared_feature_coord_envs_up = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the shared_features in the
    spin-up labeled structure
    """

    shared_feature_coord_envs_down = table_column.JSONField(blank=True, null=True)
    """
    A list of coordination environments for the shared_features in the
    spin-down labeled structure
    """

    atom_elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each atom
    in the labeled structure
    """

    atom_elf_maxima_up = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each atom
    in the spin-up labeled structure
    """

    atom_elf_maxima_down = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each atom
    in the spin-down labeled structure
    """

    electride_elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each electride
    in the labeled structure
    """

    electride_elf_maxima_up = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each electride
    in the spin-up labeled structure
    """

    electride_elf_maxima_down = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each electride
    in the spin-down labeled structure
    """

    shared_feature_elf_maxima = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each shared_feature
    in the labeled structure
    """

    shared_feature_elf_maxima_up = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each shared_feature
    in the spin-up labeled structure
    """

    shared_feature_elf_maxima_down = table_column.JSONField(blank=True, null=True)
    """
    A list of ELF maxima found at the location of each shared_feature
    in the spin-down labeled structure
    """

    separate_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the user asked to consider spin separately in this calculation
    """

    differing_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the spin up and spin down differ in the ELF and charge density
    """

    labeled_structure = table_column.JSONField(blank=True, null=True)
    """
    A JSON representing the structure labeled with various non-atomic
    features in the ELF. Features are represented with the following
    dummy atoms
    
    E: electride, Le: non-electridic bare electron, Lp: lone-pair, 
    Z: covalent bond, M: metallic feature
    """

    labeled_structure_up = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure containing information only for the spin-up
    ELF and charge density. See labeled_structure for more details
    """

    labeled_structure_down = table_column.JSONField(blank=True, null=True)
    """
    The labeled structure containing information only for the spin-down
    ELF and charge density. See labeled_structure for more details
    """

    shared_feature_atoms = table_column.JSONField(blank=True, null=True)
    """
    The nearest neighbor atoms for each covalent/metallic bond in the
    system. Values are a nested list in which the order of the lists matches
    the order of features in the structure and the values in the list
    represent the structure index of the neighbors.
    """

    shared_feature_atoms_up = table_column.JSONField(blank=True, null=True)
    """
    The nearest neighbor atoms for each covalent/metallic bond in the
    spin-up system.
    """

    shared_feature_atoms_down = table_column.JSONField(blank=True, null=True)
    """
    The nearest neighbor atoms for each covalent/metallic bond in the
    spin-down system.
    """

    shared_feature_types = table_column.JSONField(blank=True, null=True)
    """
    The type of each non-atomic and non-electridic feature in the ELF.
    Options are:
        Lp: lone-pair, Z: covalent bond, M: metal bond, Le: bare electron
    """

    bifurcation_graph = table_column.JSONField(blank=True, null=True)
    """
    The bifurcation graph representing where features appear and connect
    in the ELF
    """

    bifurcation_graph_up = table_column.JSONField(blank=True, null=True)
    """
    The bifurcation graph representing where features appear and connect
    in the spin-up ELF
    """

    bifurcation_graph_down = table_column.JSONField(blank=True, null=True)
    """
    The bifurcation graph representing where features appear and connect
    in the spin-down ELF
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
