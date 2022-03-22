This file outlines additional base_data_types that I can consider adding in the
future. For now, we are not using any of these, so they remain at the planning stage.


To guide organization and development of these...
EMMENT gives a good starting point for models
MAPIDOC gives the REST API for common endpoints (This repo is moving to API though)
    https://github.com/materialsproject/api/tree/f3a29e9faa5239d5b7642d1c295c4ff7b8d05885/src/mp_api/routes


StructureGroup (or MatchingStructures)
    This is maps to a given structure in primary structure table and links that
    structures relations to all other databases. For example, it will map to the
    list of mp-ids and icsd-ids that match the structure within a given tolerance.
    This subclasses Calculation because structure matching takes a really long time
    and even needs to be reran on occasion.
    ICSD, MP, AFLOW, JARVIS, etc...

Robocrystallogapher
    description
    condensed_structure
    mineral
    dimensionality
    
Provenance (citations)
    references
    authors
    remarks
    tags
    database_IDs (icsd, cod, etc.)
    history
    is_theoretical (bool)
    
Dielectric
    total (Total dielectric tensor)
    ionic (Ionic contribution to dielectric tensor)
    electronic (Electronic contribution to dielectric tensor)
    e_total (Total electric permittivity)
    e_ionic (Electric permittivity from atomic rearrangement)
    e_electronic (Electric permittivity due to electrons rearrangement)
    n (Refractive index)

Piezoelectric
    total (description="Total piezoelectric tensor in C/m²")
    ionic (Ionic contribution to piezoelectric tensor in C/m²)
    electronic (Electronic contribution to piezoelectric tensor in C/m²)
    e_ij_max (Piezoelectric modulus)
    max_direction (Miller direction for maximum piezo response)
    strain_for_max (Normalized strain direction for maximum piezo repsonse)

OxidationState
    structure (The structure used in the generation of the oxidation state data)
    possible_species (Possible charged species in this material)
    possible_valences (List of valences for each site in this material)
    average_oxidation_states (Average oxidation states for each unique species)
    method (Method used to compute oxidation states)

Magnetism
    ordering (Magnetic ordering)
    is_magnetic (Whether the material is magnetic)
    exchange_symmetry (Exchange symmetry)
    num_magnetic_sites (The number of magnetic sites)
    num_unique_magnetic_sites (The number of unique magnetic sites)
    types_of_magnetic_species (Magnetic specie elements)
    magmoms (Magnetic moments for each site.)
    total_magnetization (Total magnetization in μB)
    total_magnetization_normalized_vol (Total magnetization normalized by volume in μB/Å³)
    total_magnetization_normalized_formula_units (Total magnetization normalized by formula unit in μB/f.u.)

ElectronicStructure (Band Structure & DOS)
    # Both BS and DOS
    band_gap (Band gap energy in eV)
    cbm (Conduction band minimum data)
    vbm (Valence band maximum data)
    efermi (Fermi energy eV)
    is_gap_direct (Whether the band gap is direct)
    is_metal (Whether the material is a metal)
    magnetic_ordering (Magnetic ordering of the calculation)
    
    # BS
    nbands (Number of bands)
    equivalent_labels (Equivalent k-point labels in other k-path conventions)
    direct_gap (Direct gap energy in eV)
    setyawan_curtarolo (Band structure summary data using the Setyawan-Curtarolo path convention)
    hinuma (Band structure summary data using the Hinuma et al. path convention)
    latimer_munro (Band structure summary data using the Latimer-Munro path convention)
    
    # DOS
    spin_polarization (Spin polarization at the fermi level)
    total: Dict[Union[Spin, str], DosSummaryData] = Field(None, description="Total DOS summary data.")
    elemental (Band structure summary data using the Hinuma et al. path convention)
    orbital (Band structure summary data using the Latimer-Munro path convention)
    
Bonding (or Fingerprint...?)
    structure_graph (Structure graph)
    method (Method used to compute structure graph")
    bond_types (Dictionary of bond types to their length, e.g. a Fe-O to a list of the lengths of Fe-O bonds in Angstrom)
    bond_length_stats (Dictionary of statistics of bonds in structure with keys all_weights, min, max, mean and variance)
    coordination_envs (List of co-ordination environments, e.g. ['Mo-S(6)', 'S-Mo(3)'])
    coordination_envs_anonymous (List of co-ordination environments without elements present, e.g. ['A-B(6)', 'A-B(3)'])

SubstrateMatch
    substrate_id (The MPID for the substrate)
    substrate_orientation (The miller orientation of the substrate)
    substrate_formula (The formula of the substrate)
    film_orientation (The orientation of the material if grown as a film)
    matching_area (The minimal coinicidence matching area for this film orientation and substrate orientation)
    elastic_energy (The elastic strain energy)
    von_misess_strain (The Von mises strain for the film)

XRD
    spectrum # !!! it's not a spectrum
    min_two_theta
    max_two_theta
    wavelength (Wavelength for the diffraction source)
    target (Target element for the diffraction source)
    edge (Atomic edge for the diffraction source)
        K_Alpha, K_Alpha1, K_Alpha2, K_Beta, K_Beta1, K_Beta2

XAS
    spectrum
    absorbing_element
    spectrum_type (XANES, EXAFS, XAFS)
    edge (The interaction edge for XAS) (K, L2, L3, L2/3)

Electrode
    TODO: https://github.com/materialsproject/emmet/blob/main/emmet-core/emmet/core/electrode.py

Elasticity + ElesticityThirdOrder (Not from EMMET)
    (G=shear; K=bulk)
    G_Reuss
    G_VRH
    G_Voigt
    G_Voight_Reuss_Hill
    K_Reuss
    K_VRH
    K_Voight
    K_Voight_Reuss_Hill
    compliance_tensor
    elastic_anisotropy
    elastic_tensor
    elastic_tensor_original
    homogeneous_poisson	nsites
    poisson_ratio
    universal_anisotropy
    warnings
    **lots for elasticity_third_order so I haven't added these yet

# TODO:
    "grain_boundaries": ["gb_energy", "sigma", "type", "rotation_angle", "w_sep"],
    "surface_properties": [
        "weighted_surface_energy",
        "weighted_surface_energy_EV_PER_ANG2",
        "shape_factor",
        "surface_anisotropy",
        "weighted_work_function",
        "has_reconstructed",
    ],
    "eos": [],
    "phonon": [],
    "insertion_electrodes": [],
