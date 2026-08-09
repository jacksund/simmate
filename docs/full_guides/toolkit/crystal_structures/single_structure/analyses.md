# Common Analyses

--------------------------------------------------------------------------------

## Overview

Most analyses are implemented as Python methods, accepting a range of input arguments and formats. 

Since `simmate.toolkit.Structure` inherits from PyMatGen, you have access to a wealth of analysis tools built directly into the object or available via external adapters.

--------------------------------------------------------------------------------

## Unit Cell Transformations

### Sanitization

The `get_sanitized_structure` method is a Simmate-specific utility that performs a suite of common cleanup operations in a single step:

-   Converts the unit cell to its primitive form.
-   Applies LLL reduction to vectors.
-   Standardizes coordinate positions (wraps sites into the unit cell).
-   Sorts elements by electronegativity.

``` python
structure_sanitized = structure.get_sanitized_structure()
```

### Primitive and Conventional Cells

These standard transformations are provided by PyMatGen.

``` python
primitive_structure = structure.get_primitive_structure()
# Conventional cell usually requires SpacegroupAnalyzer
```

--------------------------------------------------------------------------------

## Symmetry Analysis

For detailed symmetry analysis, Simmate integrates with `SpacegroupAnalyzer` from PyMatGen, but also provides its own high-level wrappers.

``` python
# Coming soon: simpler spacegroup info access!
# For now, use the PyMatGen analyzer directly:
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

analyzer = SpacegroupAnalyzer(structure)
symbol = analyzer.get_space_group_symbol()
number = analyzer.get_space_group_number()
crystal_system = analyzer.get_crystal_system()
```

--------------------------------------------------------------------------------

## Chemical Analyses

### Neighbor Analysis

Determining which atoms are connected to each other is fundamental for many chemical analyses. Simmate leverages PyMatGen's neighbor engines.

``` python
# Find all neighbors within a specified radius
neighbors = structure.get_all_neighbors(r=3.5)

# For bonding analysis, use CrystalNN or other engines
from pymatgen.analysis.local_env import CrystalNN
cnn = CrystalNN()
bonded_sites = cnn.get_bonded_structure(structure)
```

--------------------------------------------------------------------------------
