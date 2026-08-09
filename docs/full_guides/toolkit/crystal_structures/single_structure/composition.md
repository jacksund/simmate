# Composition Class

--------------------------------------------------------------------------------

## Introduction

The `Composition` class represents the stoichiometry of a chemical system or crystal structure. It provides methods for chemical analysis, formula manipulation, and physical property estimates.

In many cases, you don't need to create a `Composition` object directly, as you can access it via the `composition` property of a `Structure` object.

--------------------------------------------------------------------------------

## Loading Compositions

To load a composition, you can use the `from_dynamic` method or initialize it directly from a string or dictionary.

``` python
from simmate.toolkit import Composition

# Initialize from a string
comp = Composition("Na2Cl2")

# Use from_dynamic for varied inputs
comp = Composition.from_dynamic("Mg2O2")
comp = Composition.from_dynamic({"Mg": 2, "O": 2})
```

--------------------------------------------------------------------------------

## Formula and Stoichiometry

A composition object provides access to various formula representations and element information.

``` python
formula = comp.formula  # e.g., "Na2 Cl2"
reduced_formula = comp.reduced_formula  # e.g., "NaCl"
elements = comp.elements  # List of unique elements
num_atoms = comp.num_atoms  # Total number of atoms
```

--------------------------------------------------------------------------------

## Physical Property Estimates

Simmate's `Composition` class includes unique methods for estimating physical properties based solely on stoichiometry.

### Radii Estimation

The `radii_estimate` method provides element-wise radii based on common models (e.g., ionic, atomic, van der waals).

``` python
# Estimated ionic radii for the elements
radii = comp.radii_estimate(radius_method="ionic")
```

### Volume and Density Estimation

Simmate can estimate the unit cell volume and density using the predicted radii and assumed packing factors.

``` python
# Estimated volume (Å³)
volume = comp.volume_estimate(radius_method="ionic", packing_factor=0.74)
```

### Element Distance Matrix

Estimate the minimum distance between different element pairs.

``` python
# Matrix of minimum element-element distances
matrix = comp.distance_matrix_estimate(packing_factor=0.5)
```

--------------------------------------------------------------------------------

## Chemical Subsystems

Determine all the smaller chemical systems that make up a larger composition.

``` python
comp = Composition("Y2C")
subsystems = comp.chemical_subsystems
# returns ["Y", "C", "C-Y"]
```

--------------------------------------------------------------------------------
