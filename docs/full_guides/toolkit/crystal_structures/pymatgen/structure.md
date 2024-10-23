# PyMatGen Structures

!!! important
    This page provides a concise list of available properties and methods, grouped by topic. 
    
    Refer to [Pymatgen's API docs](https://pymatgen.org/pymatgen.core.html) for detailed descriptions.

--------------------------------------------------------------------------------

## Molecole Loading

- `from_dict`
- `from_file`
- `from_magnetic_spacegroup`
- `from_prototype`
- `from_sites`
- `from_spacegroup`
- `from_str`

--------------------------------------------------------------------------------

## Molecole Exporting

- `as_dataframe`
- `as_dict`
- `copy`
- `to`
- `to_json`

--------------------------------------------------------------------------------

## Key Attributes

- `composition`
- `lattice`
- `sites`
- `species`
- `species_and_occu`
- `types_of_specie`
- `types_of_species`

--------------------------------------------------------------------------------

## Basic Properties

- `site_properties`
- `atomic_numbers`
- `cart_coords`
- `charge`
- `density`
- `distance_matrix`
- `formula`
- `frac_coords`
- `is_3d_periodic`
- `is_ordered`
- `is_valid`
- `num_sites`
- `pbc`
- `symbol_set`
- `volume`

--------------------------------------------------------------------------------

## Inter-structure Utils

- `interpolate`
- `matches`

--------------------------------------------------------------------------------

## Structure Modification

### Composition Transforms
- `substitute`
- `replace`
- `replace_species`

### Cell Transforms
- `apply_operation`
- `scale_lattice`
- `apply_strain`
- `make_supercell`

### Site Transforms
- `merge_sites`
- `rotate_sites`
- `translate_sites`
- `perturb`

### Charges
- `set_charge`
- `unset_charge`
- `add_oxidation_state_by_element`
- `add_oxidation_state_by_guess`
- `add_oxidation_state_by_site`
- `add_site_property`
- `add_spin_by_element`
- `add_spin_by_site`
- `remove_oxidation_states`
- `remove_site_property`
- `remove_sites`
- `remove_species`
- `remove_spin`

### List-like API
- `append`
- `count`
- `extend`
- `index`
- `insert`
- `ntypesp`
- `pop`
- `remove`
- `reverse`
- `sort`

### Other
- `relax`

--------------------------------------------------------------------------------

## Analysis Methods

- `extract_cluster`
- `group_by_types`
- `get_all_neighbors`
- `get_all_neighbors_old`
- `get_all_neighbors_py`
- `get_angle`
- `get_dihedral`
- `get_distance`
- `get_miller_index_from_site_indexes`
- `get_neighbor_list`
- `get_neighbors`
- `get_neighbors_in_shell`
- `get_neighbors_old`
- `get_orderings`
- `get_primitive_structure`
- `get_reduced_structure`
- `get_sites_in_sphere`
- `get_sorted_structure`
- `get_space_group_info`
- `get_symmetric_neighbor_list`
- `indices_from_symbol`

--------------------------------------------------------------------------------

## JSON Utils

- `unsafe_hash`
- `validate_monty_v1`
- `validate_monty_v2`

--------------------------------------------------------------------------------
