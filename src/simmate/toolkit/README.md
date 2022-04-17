
The Simmate Toolkit
--------------------

> :warning: Many classes in this module are highly experimental. We strongly recommend using [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase) for toolkit functionality until Simmate hits v1.0.0. For developers, this means many of the classes are undocumented and untested at the moment -- this facilitates our team trying different APIs/setups without spending a large amount of time reformating tests and rewriting guides. We include this experimental code on our main branch because higher-level functions (e.g. workflows) still rely on some of these features. Higher-level functions are well tested and documentated to account for changes in this module.

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
