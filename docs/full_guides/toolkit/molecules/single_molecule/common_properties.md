# Common properties

!!! important
    This page provides a concise list of available properties, grouped by function. Detailed descriptions of each property can be found in the `API` section.

!!! tip
    If you're dealing with multiple molecules, check out the "Featurizers" section for tips on enhancing speed and parallelization.

--------------------------------------------------------------------------------

## Overview

The `Molecule` class offers a wide range of accessible properties. 

You can access almost all properties like this:

``` python
n = molecule.num_atoms
```

Replace `num_atoms` with any of the options below to explore further.

--------------------------------------------------------------------------------

## Metadata & Content

- `name`
- `metadata`
- `comment`
  
!!! note
    These are only accessible when Molecules are loaded from an SDF str/file.

--------------------------------------------------------------------------------

## Composition

- `formula`
- `elements`
  
--------------------------------------------------------------------------------

## Molecular Weight

- `molecular_weight`
- `molecular_weight_exact`
- `molecular_weight_heavy_atoms`

--------------------------------------------------------------------------------

## Stereochemistry

- `num_stereocenters`

--------------------------------------------------------------------------------

## Conformers

- `num_conformers`

!!! warning
    This may be removed as conformers should be separate `Molecule` objects.

--------------------------------------------------------------------------------

## Bonding

- `num_bonds`
- `num_bonds_rotatable`
- `frac_c_sp3`

--------------------------------------------------------------------------------

## Atom counting

- `num_atoms`
- `num_atoms_heavy`
- `num_h_acceptors`
- `num_h_donors`
- `num_heteroatoms`
- `num_c_atoms`
- `num_halogen_atoms`
- `get_num_atoms_of_atomic_number()`  (method)
- `get_num_atoms_of_atomic_symbols()`  (method)

--------------------------------------------------------------------------------

## Electron counting

- `num_electrons_valence`
- `num_electrons_radical`

--------------------------------------------------------------------------------

## Rings & Aromaticity

- `num_rings`
- `num_rings_aromatic`
- `num_ring_families`
- `rings`
- `ring_sizes`
- `ring_size_min`
- `ring_size_max`
- `num_aliphatic_carbocycles`
- `num_aliphatic_heterocycles`
- `num_aromatic_heterocycles`
- `num_saturated_carbocycles`
- `num_saturated_heterocycles`
- `num_rings_saturated`

--------------------------------------------------------------------------------

## Energy States

- `max_abs_e_state_index`
- `max_e_statate_index`
- `min_abs_e_state_index`
- `min_e_state_index`

--------------------------------------------------------------------------------

## Partial Charges

- `max_abs_partial_charge`
- `max_partial_charge`
- `min_abs_partial_charge`
- `min_partial_charge`

--------------------------------------------------------------------------------

## Predicted Properties

- `log_p_rdkit`
- `tpsa_rdkit`
- `molar_refractivity_rdkit`
- `ipc`
- `synthetic_accessibility`

--------------------------------------------------------------------------------

## Substructure Components

(still under development)
Methods that map to the `smarts_sets` module will be added.

--------------------------------------------------------------------------------