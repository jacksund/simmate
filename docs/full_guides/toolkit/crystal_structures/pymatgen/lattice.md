# PyMatGen Lattices

!!! important
    This page provides a concise list of available properties and methods, grouped by topic. 
    
    Refer to [Pymatgen's API docs](https://pymatgen.org/pymatgen.core.html) for detailed descriptions.

--------------------------------------------------------------------------------

## Introduction

To access the `Lattice` object from a `Structure`:

``` python
lattice = structure.lattice  
```

--------------------------------------------------------------------------------

## Lattice Loading

### basic
- `from_dict`
- `from_parameters`

### constructors
- `cubic`
- `hexagonal`
- `monoclinic`
- `orthorhombic`
- `rhombohedral`
- `tetragonal`

--------------------------------------------------------------------------------

## Lattice Exporting

- `as_dict`
- `copy`
- `to_json`

--------------------------------------------------------------------------------

## Basic Properties

### vectors
- `a`
- `b`
- `c`
- `abc`
- `lengths`
- `pbc`

### angles
- `alpha`
- `beta`
- `gamma`
- `angles`

### full lattice
- `matrix`
- `volume`
- `is_3d_periodic`
- `is_hexagonal`
- `is_orthogonal`
- `parameters`
- `reciprocal_lattice`
- `reciprocal_lattice_crystallographic`

--------------------------------------------------------------------------------

## Measurements
- `d_hkl`
- `dot`
- `norm`

--------------------------------------------------------------------------------

## Transforms

- `inv_matrix`
- `lll_inverse`
- `lll_mapping`
- `lll_matrix`
- `metric_tensor`
- `scale`

--------------------------------------------------------------------------------

## Analysis Methods
- `get_all_distances`
- `get_brillouin_zone`
- `get_cartesian_coords`
- `get_distance_and_image`
- `get_frac_coords_from_lll`
- `get_fractional_coords`
- `get_lll_frac_coords`
- `get_lll_reduced_lattice`
- `get_miller_index_from_coords`
- `get_niggli_reduced_lattice`
- `get_points_in_sphere`
- `get_points_in_sphere_old`
- `get_points_in_sphere_py`
- `get_recp_symmetry_operation`
- `get_vector_along_lattice_directions`
- `get_wigner_seitz_cell`

--------------------------------------------------------------------------------

## Inter-lattice Utils

- `find_all_mappings`
- `find_mapping`
- `selling_dist`
- `selling_vector`

--------------------------------------------------------------------------------


## JSON Utils

- `unsafe_hash`
- `validate_monty_v1`
- `validate_monty_v2`

--------------------------------------------------------------------------------
