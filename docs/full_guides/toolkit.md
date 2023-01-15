
# The Simmate Toolkit

!!! danger
    Many classes in this module are highly experimental. We strongly recommend using [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase) for toolkit functionality until Simmate hits v1.0.0. For developers, this means many of the classes are undocumented and untested. This accelerates our testing without spending time on reformating tests and rewriting guides. We include this experimental code on our main branch because higher-level functions (e.g. workflows) rely on some of these features. Higher-level functions are well tested and documented, however, to account for ongoing low-level changes.

The toolkit module is meant to be an extension of [pymatgen](https://pymatgen.org/) and [ase](https://gitlab.com/ase/ase). It includes low-level classes and functions, such as the `Structure` class and its associated methods. The toolkit module is written entirely in python and does not use third-party DFT programs. See the `simmate.apps` module for those.

The most commonly used classes from this toolkit are the `Structure` and `Composition` classes. These classes can be imported with...

``` python
from simmate.toolkit import Structure, Composition
```


## Outline of submodules

- `base_data_types` = defines fundamental classes for materials science, including `Structure` and `Composition` classes. For convenience, these classes can be imported directly from `simmate.toolkit`, as noted above.
- `creators` = creates structures, lattices, and periodic sites
- `featurizers` = converts properties into numerical descriptors for machine-learning
- `structure_prediction` = predicts crystal structures using an evolutionary algorithm
- `symmetry` = contains tools and metadata for symmetry analyses, such as spacegroups and wyckoff sites
- `transformations` = methods to transform or "mutate" `Structures`
- `validators` = methods to check if a structure meets specific criteria
