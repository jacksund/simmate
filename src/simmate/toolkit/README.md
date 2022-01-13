
The Simmate Toolkit
--------------------

:warning: This module is highly experimental and it's use will change often. Therefore many of the classes are undocumented and untested at the moment.

The toolkit module is ment to be an extension of [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase). It includes low-level classes and functions -- such as the `Structure` class and analyses ran on it. This module is entirely in python and does not involve calling third-party DFT programs (see the `simmate.calculators` module for those).

The most commonly used classes from this toolkit are the `Structure` and `Composition` classes, which are located `base_data_types` module. For convenience, we also allow importing these classes directly with...

``` python
from simmate.toolkit import Structure, Composition
```


Outline of submodules
---------------------

- `base_data_types` = defines fundamental classes for materials science
- `creators` = creates structures, lattices, and periodic sites
- `featurizers` = makes properties into numerical descriptors for machine-learning
- `structure_prediction` = predicts reasonable crystal structures given a composition
- `symmetry` = contains tools/metadata for symmetry, such as spacegroups and wyckoff sites
- `transformations` = define transformations/mutations that can be applied to Structures
- `validators` = evulate structures/lattices/etc. to see if they meet given criteria
