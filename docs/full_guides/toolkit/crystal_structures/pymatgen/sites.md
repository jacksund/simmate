# PyMatGen Sites & Species

!!! important
    This page provides a concise list of available properties and methods, grouped by topic. 
    
    Refer to [Pymatgen's API docs](https://pymatgen.org/pymatgen.core.html) for detailed descriptions.

--------------------------------------------------------------------------------

## Introduction

Make sure you understand the difference between object classifications:

- **`Element`**: The fundamental chemical component (e.g., Na or Cl).
- **`Species`**: A singular chemical entity, encompassing an `Element`, `Ion`, `Molecule`, or `Cluster`. Essentially, a species can be an individual element or a set of associated elements. Additionally, it may contain extra information about the element(s), such as charge and bonding.
- **`Site`**: A `Species` with xyz coordinates in free space (without a lattice). It includes orientation information if multiple atoms are present in the `Species`.
- **`PeriodicSite`**: A `Species` with xyz coordinates relative to an associated lattice. This also includes orientation details if multiple atoms are part of the `Species`.

!!! example
    *(basic single crystals)* 
    
    If your `Structure` object represents the unit cell for NaCl, it contains two `PeriodicSites`: one for `Na` and one for `Cl`, both of type `Element`.

    Optionally, you can replace the `Element` types with `Ion` types: `Na+` and `Cl-`. 
    
    Since these are single-atom `Species`, there's no need to worry about orientation (i.e., rotating the atom has no effect).


!!! example
    *(advanced molecular crystals and beyond)* 
    
    If you have a crystal structure with ethanol intercalated between graphite, your `Structure` object has several ways to define its `PeriodicSites`.

    1. each atom is its own `PeriodicSite`, represented by an `Element` type
    2. there are two `PeriodicSite` types: (i) a `Molecule` type for all ethanol molecules and (ii) an `Element` type for all carbons part of the graphite.
    3. ... and more! Choose what makes sense for your application. NOTE: Options 1 and 2 should cover the majority of cases.

--------------------------------------------------------------------------------

## Periodic Sites

### Access

To access the `PeriodicSite` objects from a `Structure`:

``` python
# OPTION 1
sites = structure.sites

# OPTION 2
for site in structure:
    #... do something
```

### Loading/Exporting

- `as_dict`
- `from_dict`
- `to_json`
- `to_unit_cell`

### Position
- `x`
- `y`
- `z`
- `a`
- `b`
- `c`
- `coords`
- `frac_coords`
- `position_atol`
- `lattice` (matches between all sites in `Structure`)

### Basic Properties
- `is_ordered`
- `is_periodic_image`
- `properties`
- `specie`
- `species`
- `species_string`

### Measurements
`distance`
`distance_and_image`
`distance_and_image_from_frac_coords`
`distance_from_point`

### JSON utils
`unsafe_hash`
`validate_monty_v1`
`validate_monty_v2`

--------------------------------------------------------------------------------

## (under dev sections)

- `Element`
- `Species`

--------------------------------------------------------------------------------
