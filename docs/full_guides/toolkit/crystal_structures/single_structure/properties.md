# Common properties

--------------------------------------------------------------------------------

## Overview

The `Structure` class offers a wide range of accessible properties. Since it inherits from PyMatGen, you have access to a vast array of structural and chemical descriptors.

You can access most properties like this:

``` python
n = structure.num_sites
v = structure.volume
```

--------------------------------------------------------------------------------

## Basic Properties

These properties provide fundamental information about the structure.

| Property | Description |
| :--- | :--- |
| `num_sites` | Total number of atoms (sites) in the unit cell. |
| `formula` | Chemical formula of the structure. |
| `composition` | A `Composition` object representing the stoichiometry. |
| `volume` | Volume of the unit cell in Å³. |
| `density` | Density of the structure in g/cm³. |
| `lattice` | The `Lattice` object containing cell vectors and angles. |

--------------------------------------------------------------------------------

## Lattice Information

The `lattice` property provides detailed information about the unit cell geometry.

``` python
lattice = structure.lattice

abc = lattice.abc  # (a, b, c) lengths
angles = lattice.angles  # (alpha, beta, gamma) angles
matrix = lattice.matrix  # 3x3 lattice matrix
```

--------------------------------------------------------------------------------

## Site Information

You can iterate over the sites in a structure to access information about individual atoms.

``` python
for site in structure:
    print(site.specie)  # Element/Specie at the site
    print(site.coords)  # Cartesian coordinates
    print(site.frac_coords)  # Fractional coordinates
```

--------------------------------------------------------------------------------

## Symmetry Information

While basic symmetry info is available, more detailed analysis usually requires the `get_spacegroup_info` method (see the [Analyses](analyses.md) page).

| Property | Description |
| :--- | :--- |
| `is_ordered` | Whether the structure is fully ordered (no partial occupancy). |
| `symbol` | Space group symbol (if already determined). |

--------------------------------------------------------------------------------
